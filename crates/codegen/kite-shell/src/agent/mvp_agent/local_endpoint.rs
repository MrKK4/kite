//! Interactive connection to an unauthenticated OpenAI-compatible model server.

use super::*;
use crate::agent::config::ConfigModelOverride;
use std::num::NonZeroU64;
use std::time::Duration;

const LOCAL_CONTEXT_WINDOW: u64 = 262_144;
const LOCAL_COMPACT_AT: u64 = 230_000;

/// Accept a base URL, never an inference path or URL carrying credentials.
fn normalize_base_url(raw: &str) -> anyhow::Result<String> {
    let mut url = reqwest::Url::parse(raw.trim())?;
    anyhow::ensure!(
        matches!(url.scheme(), "http" | "https") && url.host_str().is_some(),
        "Use an http:// or https:// model server URL"
    );
    anyhow::ensure!(
        url.username().is_empty()
            && url.password().is_none()
            && url.query().is_none()
            && url.fragment().is_none(),
        "The model server URL must not contain credentials, a query, or a fragment"
    );
    let path = url.path().trim_end_matches('/');
    anyhow::ensure!(
        !path.ends_with("/chat/completions") && !path.ends_with("/models"),
        "Use the API base URL, for example http://localhost:8080/v1"
    );
    let path = if path.is_empty() { "/v1" } else { path }.to_owned();
    url.set_path(&path);
    Ok(url.to_string().trim_end_matches('/').to_owned())
}

#[derive(serde::Deserialize)]
struct ModelsResponse {
    data: Vec<DiscoveredModel>,
}

#[derive(serde::Deserialize)]
struct DiscoveredModel {
    id: String,
}

fn local_models(
    base_url: &str,
    response: ModelsResponse,
) -> anyhow::Result<IndexMap<String, ConfigModelOverride>> {
    let mut models = IndexMap::new();
    for model in response.data {
        let id = model.id.trim();
        if id.is_empty() {
            continue;
        }
        models.insert(
            format!("local:{id}"),
            ConfigModelOverride {
                model: Some(id.to_owned()),
                name: Some(id.to_owned()),
                system_prompt_label: Some("Kite".into()),
                base_url: Some(base_url.to_owned()),
                // Explicit provider-owned placeholder prevents falling back to an
                // xAI session token or XAI_API_KEY on an unauthenticated server.
                api_key: Some("none".into()),
                api_backend: Some(crate::sampling::ApiBackend::ChatCompletions),
                context_window: Some(LOCAL_CONTEXT_WINDOW),
                auto_compact_at_tokens: NonZeroU64::new(LOCAL_COMPACT_AT),
                auto_compact_threshold_percent: Some(88),
                max_completion_tokens: Some(32_768),
                supports_reasoning_effort: Some(false),
                supports_backend_search: Some(false),
                stream_tool_calls: Some(false),
                ..Default::default()
            },
        );
    }
    anyhow::ensure!(
        !models.is_empty(),
        "The server returned no model IDs in /models"
    );
    Ok(models)
}

async fn discover(base_url: &str) -> anyhow::Result<IndexMap<String, ConfigModelOverride>> {
    let response = crate::http::shared_client()
        .get(format!("{base_url}/models"))
        .timeout(Duration::from_secs(30))
        .send()
        .await?
        .error_for_status()?
        .json::<ModelsResponse>()
        .await?;
    local_models(base_url, response)
}

/// `kite login <url>`: discover and persist the endpoint before the TUI starts,
/// so the launched session picks it up from `config.toml`. Returns the default model.
pub async fn save_endpoint_from_cli(raw_url: &str) -> anyhow::Result<String> {
    let base_url = normalize_base_url(raw_url)?;
    let models = discover(&base_url).await?;
    let default = models.first().expect("nonempty model list").0.clone();
    crate::util::config::save_local_endpoint(models, default.clone()).await?;
    Ok(default)
}

impl MvpAgent {
    pub(super) async fn login_local_endpoint(
        &self,
        raw_url: &str,
    ) -> Result<AuthenticateResponse, acp::Error> {
        self.configure_local_endpoint(raw_url).await.map_err(|e| {
            acp::Error::invalid_params().data(format!("Local model connection failed: {e}"))
        })
    }

    async fn configure_local_endpoint(
        &self,
        raw_url: &str,
    ) -> anyhow::Result<AuthenticateResponse> {
        let base_url = normalize_base_url(raw_url)?;
        // A dedicated request without a bearer: never send saved account
        // credentials to the user-supplied endpoint, including across redirects.
        let models = discover(&base_url).await?;
        let default = models.first().expect("nonempty model list").0.clone();
        let mut cfg = self.cfg.borrow().clone();
        // A new tunnel URL replaces the previous endpoint's models instead of
        // leaving dead `local:*` entries selectable.
        cfg.config_models.retain(|key, _| !key.starts_with("local:"));
        cfg.config_models.extend(models.clone());
        cfg.models.default = Some(default.clone());
        cfg.models.default_is_campaign_driven = false;
        cfg.models.default_reasoning_effort = None;
        cfg.models.session_summary = Some(default.clone());
        cfg.models.image_description = Some(default.clone());
        cfg.models.prompt_suggestion = Some(default.clone());
        cfg.session_summary_model = Some(default.clone());
        cfg.image_description_model = Some(default.clone());
        cfg.disable_web_search = true;
        cfg.validate_model_filters()
            .map_err(|e| anyhow::anyhow!(e.to_string()))?;
        let catalog = crate::agent::remote_config::resolve_model_catalog(&cfg, None);
        anyhow::ensure!(
            catalog
                .get(&default)
                .is_some_and(|m| m.info.user_selectable),
            "The discovered model is excluded by the configured model allowlist"
        );
        // Discovery and validation finish before either persistent or live config changes.
        crate::util::config::save_local_endpoint(models, default.clone()).await?;
        *self.cfg.borrow_mut() = cfg.clone();
        self.models_manager.apply_config_reselecting_default(cfg);
        self.models_manager
            .set_current_model_id(acp::ModelId::new(default));
        self.models_manager.set_current_reasoning_effort(None);
        *self.sampling_config.borrow_mut() = self.models_manager.sampling_config();
        self.set_auth_method(acp::AuthMethodId::new(auth_method::XAI_API_KEY_METHOD_ID));
        // Do not publish the placeholder as a credential for hosted side services.
        let state = self.model_state(None);
        let meta = serde_json::json!({
            "auth_mode": "api_key",
            "backend_billed": true,
            "local_models": state,
        });
        Ok(AuthenticateResponse::default().meta(meta.as_object().cloned()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn discovery_uses_models_endpoint_without_account_credentials() {
        use tokio::io::{AsyncReadExt, AsyncWriteExt};
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let url = format!("http://{}/v1", listener.local_addr().unwrap());
        let server = tokio::spawn(async move {
            let (mut stream, _) = listener.accept().await.unwrap();
            let mut request = Vec::new();
            loop {
                let byte = stream.read_u8().await.unwrap();
                request.push(byte);
                if request.ends_with(b"\r\n\r\n") {
                    break;
                }
            }
            let request = String::from_utf8(request).unwrap().to_ascii_lowercase();
            assert!(request.starts_with("get /v1/models http/1.1"));
            assert!(!request.contains("authorization:"));
            let body = r#"{"data":[{"id":"qwen-local"}]}"#;
            let response = format!(
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
                body.len()
            );
            stream.write_all(response.as_bytes()).await.unwrap();
        });
        let models = discover(&url).await.unwrap();
        assert_eq!(models.first().unwrap().0, "local:qwen-local");
        server.await.unwrap();
    }

    #[test]
    fn normalizes_local_api_urls() {
        assert_eq!(
            normalize_base_url("http://localhost:8080").unwrap(),
            "http://localhost:8080/v1"
        );
        assert_eq!(
            normalize_base_url("https://example.test/proxy/v1/").unwrap(),
            "https://example.test/proxy/v1"
        );
        for invalid in [
            "file:///tmp/model",
            "https://user:secret@example.test/v1",
            "https://example.test/v1?key=secret",
            "http://localhost/v1/chat/completions",
        ] {
            assert!(normalize_base_url(invalid).is_err(), "{invalid}");
        }
    }

    #[test]
    fn discovers_models_with_local_compatibility_and_compaction() {
        let response = serde_json::from_value(serde_json::json!({
            "data": [{"id": "Qwen3", "object": "model"}, {"id": ""}, {"id": "Qwen3"}, {"id": "second"}]
        })).unwrap();
        let models = local_models("http://localhost:8080/v1", response).unwrap();
        assert_eq!(models.len(), 2);
        let (key, model) = models.first().unwrap();
        assert_eq!(key, "local:Qwen3");
        assert_eq!(model.api_key.as_deref(), Some("none"));
        assert_eq!(model.context_window, Some(262_144));
        assert_eq!(
            model.auto_compact_at_tokens.map(NonZeroU64::get),
            Some(230_000)
        );
        assert_eq!(model.supports_reasoning_effort, Some(false));
        assert!(local_models("http://localhost/v1", ModelsResponse { data: vec![] }).is_err());
    }
}

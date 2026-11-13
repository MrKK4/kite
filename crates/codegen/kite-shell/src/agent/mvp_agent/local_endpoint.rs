//! Interactive connection to an unauthenticated OpenAI-compatible model server.

use super::*;
use crate::agent::config::ConfigModelOverride;
use std::num::NonZeroU64;
use std::time::Duration;

/// Fallback when the server does not report its context size.
const LOCAL_CONTEXT_WINDOW: u64 = 262_144;
/// Compact at this share of the server's context window.
const LOCAL_COMPACT_PERCENT: u64 = 88;

fn compact_at(context_window: u64) -> u64 {
    context_window * LOCAL_COMPACT_PERCENT / 100
}

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
    /// vLLM reports the served context length here.
    #[serde(default)]
    max_model_len: Option<u64>,
    /// llama.cpp reports the model's training context here.
    #[serde(default)]
    meta: Option<ModelMeta>,
}

#[derive(serde::Deserialize)]
struct ModelMeta {
    #[serde(default)]
    n_ctx_train: Option<u64>,
}

fn local_models(
    base_url: &str,
    response: ModelsResponse,
    server_context: Option<u64>,
) -> anyhow::Result<IndexMap<String, ConfigModelOverride>> {
    let mut models = IndexMap::new();
    for model in response.data {
        // The server's configured context (llama.cpp /props) wins; then what /models reports.
        let context_window = server_context
            .or(model.max_model_len)
            .or(model.meta.as_ref().and_then(|m| m.n_ctx_train))
            .filter(|&n| n >= 4_096)
            .unwrap_or(LOCAL_CONTEXT_WINDOW);
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
                context_window: Some(context_window),
                auto_compact_at_tokens: NonZeroU64::new(compact_at(context_window)),
                auto_compact_threshold_percent: Some(LOCAL_COMPACT_PERCENT as u8),
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
    local_models(base_url, response, server_context(base_url).await)
}

/// llama.cpp's configured context (`n_ctx` from `/props` at the server root). Best effort.
async fn server_context(base_url: &str) -> Option<u64> {
    let root = base_url.strip_suffix("/v1").unwrap_or(base_url);
    let props: serde_json::Value = crate::http::shared_client()
        .get(format!("{root}/props"))
        .timeout(Duration::from_secs(10))
        .send()
        .await
        .ok()?
        .error_for_status()
        .ok()?
        .json()
        .await
        .ok()?;
    props
        .pointer("/default_generation_settings/n_ctx")
        .or_else(|| props.get("n_ctx"))
        .and_then(serde_json::Value::as_u64)
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
        let models = local_models("http://localhost:8080/v1", response, None).unwrap();
        assert_eq!(models.len(), 2);
        let (key, model) = models.first().unwrap();
        assert_eq!(key, "local:Qwen3");
        assert_eq!(model.api_key.as_deref(), Some("none"));
        assert_eq!(model.context_window, Some(262_144));
        assert_eq!(
            model.auto_compact_at_tokens.map(NonZeroU64::get),
            Some(230_686)
        );
        assert_eq!(model.supports_reasoning_effort, Some(false));
        assert!(local_models("http://localhost/v1", ModelsResponse { data: vec![] }, None).is_err());
    }

    #[test]
    fn compaction_follows_the_server_context_size() {
        let response = || {
            serde_json::from_value::<ModelsResponse>(serde_json::json!({
                "data": [{"id": "q", "meta": {"n_ctx_train": 262144}, "max_model_len": 65536}]
            }))
            .unwrap()
        };
        // llama.cpp /props (configured n_ctx) wins over what /models reports.
        let (_, m) = local_models("u", response(), Some(131_072)).unwrap().shift_remove_index(0).unwrap();
        assert_eq!(m.context_window, Some(131_072));
        assert_eq!(m.auto_compact_at_tokens.map(NonZeroU64::get), Some(115_343));
        // Without /props, vLLM's max_model_len is used.
        let (_, m) = local_models("u", response(), None).unwrap().shift_remove_index(0).unwrap();
        assert_eq!(m.context_window, Some(65_536));
        assert_eq!(m.auto_compact_at_tokens.map(NonZeroU64::get), Some(57_671));
    }
}

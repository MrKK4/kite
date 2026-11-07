use crate::app::actions::Action;
use crate::slash::command::{AppCtx, CommandExecCtx, CommandResult, SlashCommand, slash_meta};

pub struct LoginCommand;

impl SlashCommand for LoginCommand {
    slash_meta! {
        name: "login",
        description: "Connect an OpenAI-compatible local model endpoint",
        usage: "/login http(s)://host/v1",
        takes_args: true,
    }

    fn visible(&self, _ctx: &AppCtx) -> bool {
        true
    }

    fn run(&self, _ctx: &mut CommandExecCtx, args: &str) -> CommandResult {
        let url = args.trim();
        if url.is_empty() {
            return CommandResult::Error("Usage: /login http(s)://host/v1".into());
        }
        if !(url.starts_with("http://") || url.starts_with("https://"))
            || url.chars().any(char::is_whitespace)
        {
            return CommandResult::Error("Usage: /login http(s)://host/v1".into());
        }
        CommandResult::Action(Action::LoginEndpoint(url.to_owned()))
    }
}

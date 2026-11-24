# Last Reply

A [herdr](https://herdr.dev) plugin that shows when each agent last replied, next to the agent and next to its Space.

- When an agent finishes a turn (it goes from working to done, idle or blocked), its pane gets a `$last` token with the time, e.g. `4:32 PM`.
- The pane's Space gets the same token, so a Space shows the latest reply of any agent in it.
- A reply from an earlier day shows the weekday too, e.g. `Mon 11:05 AM`.

It runs on herdr startup and whenever an agent changes status. No background process.

Requires herdr 0.9.5+ and `python3`. Linux and macOS.

## Quick start

1. Install the plugin:

   ```bash
   herdr plugin install Ars-Paulina/herdr-last-reply
   ```

2. Show the time. The plugin only sets the token; your sidebar layout decides where it appears. Add a `$last` entry to the rows in herdr's `config.toml`, for example at the end of the first row:

   ```toml
   [ui.sidebar.agents]
   rows = [
     ["state_icon", "workspace", { token = "$last", fg = "#6c7086" }],
     ["terminal_title_stripped"],
   ]

   [ui.sidebar.spaces]
   rows = [
     ["state_icon", "workspace", { token = "$last", fg = "#6c7086" }],
   ]
   ```

   Agents and Spaces without a reply yet skip the token.

3. Apply the config:

   ```bash
   herdr server reload-config
   ```

## Notes

- Times start from when the plugin is installed: an agent shows a time after its next reply.
- The time is written once per reply, so the weekday in `Mon 11:05 AM` is set when the reply happens, not updated later.
- herdr's web UI (Ovis) shows the agent token in its Agents list. Space tokens are not drawn there yet; see [devswha/ovis#4627](https://github.com/devswha/ovis/issues/4627).

## Update

```bash
herdr plugin update last-reply
```

## Uninstall

```bash
herdr plugin uninstall last-reply
```

Then remove the `$last` entries from your `config.toml`.

## Development

Self-check: `python3 last_reply.py --test`.

## License

MIT. See [LICENSE](LICENSE).

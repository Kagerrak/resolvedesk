# S08 connector preparation (not implementation or verification)

19 November 2026. No Google OAuth credentials/token encryption key are configured in this checkout. User setup choice is pending. No mailbox has been accessed and no resources provisioned.

Official sources inspected through ego-browser:
- https://developers.google.com/workspace/gmail/api/auth/scopes
- https://developers.google.com/workspace/gmail/api/guides/sync
- https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.history/list
- https://developers.google.com/identity/protocols/oauth2/web-server

Implementation direction: request Gmail read-only access for S08; no modify/send scope. This reads message bodies and grants mailbox-wide provider access: selected-label isolation is application-enforced and must be stated accurately. Metadata-only access cannot import reply content. Public visitors cannot connect; require authenticated nonanonymous staff Admin in a live workspace.

Use maintained OAuth library, server-side client secret and encrypted refresh/access tokens. Bind expiring one-use state to staff session/workspace/fixed redirect; request offline access; validate actual granted scopes and mailbox identity. Never return tokens to browser/logs or public evidence. Separate staff sign-in and mailbox consent.

Initial sync reads only selected label with all pages, scoped message/thread identities and a bounded durable job. Incremental history consumes all pages from committed cursor; only advance cursor with ingested data. History expiry returns 404 and needs deduplicated full resync. Do not infer history numbers are contiguous. Recheck each fetched message still carries label, reject outbound/SENT/self sender, maintain unique provider IDs per connection and ticket locks/revision changes for imports. No hidden thread expansion to unrelated unlabeled messages.

Disconnect must fence workers, clear encrypted local tokens and attempt revocation. Revocation failure must not silently reconnect or retain local usable credentials. Reconnect must not switch mailbox identity over existing mappings. Provider errors need safe status, saved cursor and explicit recovery; no arbitrary provider endpoints.

Before real verification: user configures OAuth test users + dedicated synthetic mailbox and local ignored credentials; establish staff membership; encrypted-token key never committed. Google testing/verification constraints must be checked before any hosted/public connector claim. S08 cannot be called delivered until genuine dedicated-mailbox journey is documented without private identifiers/content in Git.

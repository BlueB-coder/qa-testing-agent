# Security

Do not include credentials, customer records, browser state, private endpoints or
unredacted execution artifacts in public issues or pull requests.

For a vulnerability, use GitHub private vulnerability reporting if enabled on the
published repository, or contact its maintainer through an established private channel.
Until publication, send findings through the repository owner's existing private
channel. There is no invented support email or active hosted service.

The kit provides behavioral QA restrictions, not an OS sandbox or credential store.
Use host access controls and isolated test mounts where stronger enforcement is
needed. Never run mutating QA on production or an unverified shared environment.
The external write approval gate also depends on the host/integration honoring it.

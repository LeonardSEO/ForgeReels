# Facts: how a website remembers you

| Claim | Source |
|---|---|
| After a login the server sends a cookie (a small piece of data) in a Set-Cookie response header | MDN, "Using HTTP cookies" (https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies) |
| The browser stores it and sends it back with later requests to that site | same page |
| The server uses it to recognise the session ("knows it's you") | same page, "session management" |

The cookie values on screen (session id, 30 days) are illustrative and shown as an example.

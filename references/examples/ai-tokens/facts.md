# Facts: how a language model writes its answer

| Claim | Source |
|---|---|
| Text is split into tokens (pieces of words) before a model reads it | OpenAI Help Center, "What are tokens and how to count them?" (https://help.openai.com/en/articles/4936856) |
| Each token is turned into a vector of numbers (an embedding) | Wikipedia, "Large language model", tokenization and embeddings |
| The model predicts the next token; it is appended and the process repeats (autoregressive generation) | Wikipedia, "Large language model" |

The six bars and their values are an illustration of "a list of numbers", labelled as such on screen.

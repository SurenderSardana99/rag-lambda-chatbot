# RAG Chatbot on AWS Lambda

A serverless Retrieval-Augmented Generation (RAG) chatbot: ingest documents
into a vector index, retrieve relevant context at query time, and generate
grounded, source-cited answers via an LLM — all running on AWS Lambda behind
API Gateway.

**Author:** Surender Sardana — Senior Data/AI Engineer

I built this as a hands-on reference implementation of a serverless GenAI
pattern I work with regularly: RAG retrieval, grounded prompt design to
reduce hallucination, and an AWS-native deployment (Lambda, API Gateway, S3,
IAM) provisioned entirely through Terraform. It's intentionally scoped small
so the architecture and design decisions are easy to review end-to-end,
rather than being a large production codebase.

## Architecture

```
                 ┌─────────────────┐
   POST /chat    │  API Gateway     │
  ─────────────► │  (HTTP API)      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌─────────────────┐        ┌──────────────────┐
                 │  AWS Lambda      │◄──────►│  S3: FAISS index  │
                 │  (handler.py)    │        │  (vector store)   │
                 └────────┬─────────┘        └──────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Anthropic API   │
                 │  (LLM generate)  │
                 └─────────────────┘
```

**Flow:**
1. User question hits API Gateway → routed to Lambda.
2. `Retriever` embeds the question and searches a FAISS index for the top-k
   relevant chunks (index is pre-built offline and stored in S3).
3. `build_prompt` assembles a grounded prompt: retrieved context + question +
   explicit instruction not to answer beyond the given context.
4. `LLMClient` calls the LLM and returns the answer along with the source
   documents used — so answers are traceable and hallucinations are easier
   to catch.

## Project Structure

```
src/
  handler.py          Lambda entry point
  rag/
    retriever.py      FAISS-based similarity search
    llm_client.py      LLM API wrapper
    prompt.py          Grounded prompt construction
scripts/
  build_index.py       Offline script to build the vector index
infra/
  main.tf              Lambda, API Gateway, IAM, S3 (Terraform)
  variables.tf
  outputs.tf
tests/
  test_prompt.py        Unit tests
.github/workflows/
  ci.yml                 Test + Terraform lint on push
```

## Local Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY=your_key_here

# Build the vector index from sample docs
python scripts/build_index.py --input docs/ --output index/faiss_index

# Run tests
pytest tests/ -v
```

## Deploying

```bash
# Package the Lambda
pip install -r requirements.txt -t build/package
cp -r src/* build/package/
cd build/package && zip -r ../lambda_package.zip . && cd ../..

# Deploy infrastructure
cd infra
terraform init
terraform apply -var="anthropic_api_key=$ANTHROPIC_API_KEY"
```

## Design Decisions

- **Grounding over free generation** — the prompt explicitly instructs the
  model to answer only from retrieved context and to admit when it can't,
  directly addressing the hallucination concern called out in most GenAI
  role requirements.
- **Swappable LLM provider** — `LLMClient` isolates the Anthropic API call so
  swapping to Bedrock or another provider touches one file, not the whole
  pipeline.
- **Offline index build** — keeps the Lambda's cold start fast; the index is
  built once (or on a schedule) and pulled from S3 rather than rebuilt per
  request.
- **IaC-first deployment** — all infrastructure (Lambda, API Gateway, IAM,
  S3) is defined in Terraform so environments are reproducible.

## Possible Extensions

- Swap FAISS for OpenSearch/Pinecone for a managed, scalable vector store.
- Add conversation memory (multi-turn context) via DynamoDB session storage.
- Add a LangGraph-based agent layer for multi-step tool use on top of RAG.
- Add Speech-to-Text/Text-to-Speech (Amazon Transcribe/Polly) for a voice
  interface — relevant for contact-center style GenAI applications, similar
  to a voice-agent UI I previously built for a real-estate use case using
  the Web Speech API and the Anthropic API.

## About Me

Senior Data/AI Engineer with 10+ years across .NET/C#, Python, data
engineering, and cloud platforms (AWS, Azure, GCP), including RAG systems,
LLM integration, and enterprise integration work.

- GitHub: [SurenderSardana99](https://github.com/SurenderSardana99)
- Email: surendersardana99@gmail.com

## License

MIT — see [LICENSE](LICENSE)

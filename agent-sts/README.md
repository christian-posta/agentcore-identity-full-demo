Run agent sts:

```bash
agent-sts -config config/config.yaml
```

Run with docker:

```bash
docker run --rm -p 8080:8080 -v ./config.yaml:/app/config/config.yaml ceposta/agent-sts:latest
```
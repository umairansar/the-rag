## Restart services (clear ports first)

```bash
# Kill all services
fuser -k 8001/tcp
fuser -k 8501/tcp
sudo docker rm -f inngest

# Restart
sudo docker run -d -p 8288:8288 --name inngest inngest/inngest inngest dev -u http://172.17.0.1:8001/api/inngest
sleep 2 && nohup uv run hypercorn main:app --bind "0.0.0.0:8001" > hypercorn.log 2>&1 &
sleep 2 && nohup uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
```

## Start services

```bash
# Inngest
# Note: 172.17.0.1 = Docker bridge gateway (Linux/EC2 only). On Windows/Mac use host.docker.internal instead.
sudo docker run -d -p 8288:8288 --name inngest inngest/inngest inngest dev -u http://172.17.0.1:8001/api/inngest

# FastAPI
nohup uv run hypercorn main:app --bind "0.0.0.0:8001" > hypercorn.log 2>&1 &

# Streamlit
nohup uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
```

## Local services

```bash
# Inngest
# Note: 172.17.0.1 = Docker bridge gateway (Linux/EC2 only). On Windows/Mac use host.docker.internal instead.
docker run -d -p 8288:8288 --name inngest inngest/inngest inngest dev -u http://host.docker.internal:8001/api/inngest

# FastAPI
uv run uvicorn main:app --host 0.0.0.0 --port 8001

# Streamlit
uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0  
```

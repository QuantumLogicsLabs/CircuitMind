FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn groq python-dotenv schemdraw
EXPOSE 7860
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "7860"]

# ---------- Base Image ----------
FROM python:3.10.11

# ---------- Install System Deps ----------
RUN apt-get update && apt-get install -y git build-essential

# ---------- Set Working Directory ----------
WORKDIR /app

# ---------- Copy Project Files ----------
COPY . .

# ---------- Install Python Deps ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Make start.sh executable ----------
RUN chmod +x start.sh

# ---------- Expose Ports ----------
EXPOSE 5005
EXPOSE 5055

# ---------- Start Script ----------
CMD ["bash", "start.sh"]
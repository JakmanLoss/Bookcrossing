# Используем официальный образ Python 3.9
FROM python:3.9-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Создаем папку для загрузок обложек
RUN mkdir -p static/uploads

# Указываем переменные окружения (если нужно)
ENV FLASK_ENV=production
ENV SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Команда для запуска приложения
CMD ["flask", "run", "--host=0.0.0.0"]
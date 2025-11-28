docker compose up -d postgres

docker run --rm -it -p 4566:4566 localstack/localstack

python manage.py migrate
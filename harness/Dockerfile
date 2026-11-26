# Rota alternativa: roda scripts/{up,down,gates}.sh dentro de um container
# para hosts sem bash ou sem Docker Compose v2. Só exige Docker Engine;
# fala com o daemon do host pelo socket montado.
FROM docker:27-cli
RUN apk add --no-cache bash curl
ENTRYPOINT ["bash"]

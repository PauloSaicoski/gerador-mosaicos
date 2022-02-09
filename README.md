# Gerador de Mosaicos

Adaptação do código desenvolvido para o TCC Construção de Mosaicos de Imagens Digitais para a Gerência de Patologias em Estruturas de Difícil Acesso para ser utilizado com container docker

## Descrição

O trabalho consiste em um gerador de imagens panorâmicas, mosaicos. O usuário informa as imagens a serem unidas e a ferramenta cria os mosaicos. A ferramenta descobre também a ordenação das imagens e quantos mosaicos devem ser criados.

## Instruções

A imagem docker pode ser construída a partir do seguinte comando:
```bash
docker build -t mosaico_docker ./docker/
```

Para executar a criação dos mosaicos, numa pasta que contenha as imagens a serem unidas, utilize o script run_container.sh disponivel na pasta [bash_script](https://github.com/PauloSaicoski/gerador-mosaicos/tree/main/bash_script). Será requisitada a senha do usuário para a alteração das permissões de edição dos arquivos criados pelo container.

## Notas

- É necessário que a imagem docker criada se chame mosaico_docker para que o arquivo run_container.sh funcione;
- Caso o container precise de mais memória, devido a imagens pesadas, é possível específicar a quantia de memória utilizada pelo container a partir da opção -m no comando de build

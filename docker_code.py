#!/usr/bin/env python3
import datetime
import cv2
import os
import sys

sys.path.insert(1, '../')
import mosaic_generator as mg


if __name__ == "__main__":

    # inicializa variaveis
    folderPath = "./fotos"
    photosPaths=[]
    fotos = []

    photosNames = os.listdir(folderPath)
    photosNames = mg.filtraImagens(photosNames)

    for name in photosNames:
        imagem = mg.Foto(f'{folderPath}/{name}', name)
        photosPaths.append(f'{folderPath}/{name}')
        fotos.append(imagem)


    # atualiza o diretorio inicial das janelas de selecao
    diretorio = folderPath

    ordens = mg.encontraOrdem(fotos)
    indicesEscolhidos = [-1 for _ in ordens]

    mosaicos = mg.criaMosaicos(fotos, ordens, indicesEscolhidos)

    for i in range(len(mosaicos)):
        x = datetime.datetime.now()
        caminho = f'./fotos/{x.strftime("%d%m%Y_%H%M%S")}_{i}'
        os.makedirs(caminho)
        cv2.imwrite(caminho+"/mosaico.png", mosaicos[i])
        texto = []
        texto.append(f'O arquivo "mosaico.png" foi confeccionado utilizando as seguintes imagens:\n')
        texto = texto + [nome+'\n' for nome in mg.descobreNomesOrdem(ordens[i], fotos)]
        # o arquivo de texto contem os nomes das imagens utilizadas no mosaico
        with open(caminho+"/imagens_utilizadas.txt", 'w') as arquivoTxt:
            arquivoTxt.writelines(texto)


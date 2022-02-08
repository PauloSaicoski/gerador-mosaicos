#!/usr/bin/env python3
import datetime
import sys
import cv2
import numpy as np
import os
import math

MIN_MATCH_COUNT = 10
QTD_PONTOS_CHAVE = 2000
DISTANCE_THRESHOLD = 0.57
PROPORCAO_IMAGENS = 0.2
MAX_IMAGE_SIZE_SELECTOR = 500
MAX_IMAGE_SIZE_MOSAICOS = 900

class Foto:
    def __init__(self, caminhoImg, nome, nfeatures = QTD_PONTOS_CHAVE):
        self.nome = nome
        self.imagem = cv2.imread(caminhoImg) # carrega a imagem
        orb = cv2.ORB_create(nfeatures = nfeatures)
        self.tamanho = self.imagem.shape[:2]
        deslocMaskX = round(self.tamanho[1]*0.15) # define o recuo da mascara
        deslocMaskY = round(self.tamanho[0]*0.075)
        # gera a mascara
        mask = cv2.rectangle(np.zeros(self.tamanho, dtype='uint8'),(deslocMaskX,deslocMaskY),(self.tamanho[1]-deslocMaskX,self.tamanho[0]-deslocMaskY),255,-1)
        self.kpCentral, self.dcCentral = orb.detectAndCompute(self.imagem, mask) 
        # calcula os pontos chave e descritores da regiao central
        self.kpTotal, self.dcTotal = orb.detectAndCompute(self.imagem, None)     
        # e da regiao total

    def exibeImagemKP(self, proporcao = 0.4): # exibe a imagem com seus pontos chave
        imagem = cv2.drawKeypoints(self.imagem, self.kpCentral, None, (255, 0, 255))
        cv2.imshow(self.nome, cv2.resize(imagem,(0,0),None,proporcao,proporcao)) 
        return imagem

# filtra matches distintos o suficiente
filtraLMatches = lambda matches : [m for m,n in matches if m.distance < DISTANCE_THRESHOLD * n.distance] 

def encontraMatches(img1, img2):
    # funcao baseada nos procedimentos descritos por datahacker.rs

    bf = cv2.BFMatcher_create(cv2.NORM_HAMMING) 
    
    # utilizando apenas pontos chave da regiao central
    # encontra os 2 matches de img2 mais proximos de cada ponto chave de img1
    matchesCentral = bf.knnMatch(img1.dcCentral, img2.dcCentral, k=2) 
    # filtra apenas os matches com determinada distincao entre o mais proximo e segundo mais proximo
    goodCentral = filtraLMatches(matchesCentral) 
    if (len(goodCentral) > MIN_MATCH_COUNT):
        return 0, goodCentral

    # repete o processo para pontos chave da regiao total da imagem
    matchesTotal = bf.knnMatch(img1.dcTotal, img2.dcTotal, k=2)
    goodTotal = filtraLMatches(matchesTotal)
    if (len(goodTotal) > MIN_MATCH_COUNT):
        return 1, goodTotal

    return -1, None

def encontraOrdem(lista, _naoVisitados = None):
    # caso seja uma recursao, parte apenas das imagens nao visitada
    if(_naoVisitados == None):
        naoVisitados = [*range(len(lista))]
    else:
        naoVisitados = _naoVisitados
    
    visitados = []
    visitados.append(naoVisitados.pop(0)) # a primeira imagem da lista eh visitada automaticamente
    ordem = []

    # o primeiro laco tenta aproveitar as imagens ja ordenadas
    for visitado in visitados:
        if(len(naoVisitados)>0):
            regiao, matches = encontraMatches(lista[naoVisitados[0]], lista[visitado])
            if(regiao >= 0):
                ordem.append((visitado, naoVisitados[0], regiao, matches))
                visitados.append(naoVisitados.pop(0))
    
    # o segundo laco compara todas as imagens nao visitadas com aquelas que foram adicionadas ao mosaico
    ocorreuAdicao = True
    while(ocorreuAdicao):
        ocorreuAdicao = False
        for naoVisitado in naoVisitados:
            for visitado in reversed(visitados):
                regiao, matches = encontraMatches(lista[naoVisitado], lista[visitado])
                if(regiao >= 0): 
                    # toda vez que uma area de sobreposicao aceitavel eh encontrada
                    # o par de imagens eh armazenado juntamente com a lista de correspondencias de pontos chave
                    ordem.append((visitado, naoVisitado, regiao, matches)) 
                    visitados.append(naoVisitados.pop(naoVisitados.index(naoVisitado)))
                    ocorreuAdicao = True
                    break
    
    print("Restam ", len(naoVisitados), "imagens")
    resultado = []
    if (len(ordem) > 0):
        resultado.append(ordem)
    if (len(naoVisitados)>1):
        # caso ainda haja imagens em naoVisitados, chama uma recursao que possibilita a criacao de mais mosaicos
        ordemRecursao = encontraOrdem(lista, naoVisitados)
        if(len(ordemRecursao)>0):
            resultado = resultado + ordemRecursao

    return resultado

def retornaPontosCoincidentes(img1, img2, regiao, matches):
    # funcao baseada nos procedimentos descritos por datahacker.rs

    # funcao para utilizar os pontos chave correspondentes entre duas imagens
    # leva em consideracao se foram utilizados pontos da regiao central ou total das imagens
    if(regiao == 0):
        pontos1 = [img1.kpCentral[m.queryIdx] for m in matches]
        pontos2 = [img2.kpCentral[m.trainIdx] for m in matches]
    elif(regiao == 1):
        pontos1 = [img1.kpTotal[m.queryIdx] for m in matches]
        pontos2 = [img2.kpTotal[m.trainIdx] for m in matches]

    return pontos1, pontos2

def calculaMatrizH(kp1, kp2): 
    # funcao baseada nos procedimentos descritos por datahacker.rs

    # recebe os pontos chave correspondentes e cria a matriz de transformacao
    src_pts = np.float32([ kp1[x].pt for x in range(len(kp1))]).reshape(-1,1,2)
    dst_pts = np.float32([ kp2[x].pt for x in range(len(kp2))]).reshape(-1,1,2)
    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    return H


def mergeImages(imgList, ordem, indice): # cria um mosaico
    # funcao baseada nos procedimentos descritos por datahacker.rs e por MathWorks

    def encontraIndiceLocal(indiceGlobal):
        if(indiceGlobal == ordem[0][0]):
            return 0
        for i in range(len(ordem)):
            if(ordem[i][1] == indiceGlobal):
                return i+1
        print("indice local não encontrado")
        sys.exit()

    # declaracao de variaveis
    qntImgs = len(ordem)+1
    hList = [np.identity(3) for _ in range(qntImgs)] # lista de matrizes de transformacao
    rows, cols = imgList[ordem[0][0]].tamanho
    limitesAtuais = [] # armazena os limites iniciais de cada imagem
    limitesFinais = [] # armazena os limites de cada imagem apos as tranformacoes
    # armazena as informacoes da primeira imagem
    limitesAtuais.append(np.float32([[0,0], [0, rows],[cols, rows], [cols, 0]]).reshape(-1, 1, 2))
    limitesFinais.append(limitesAtuais[0])

    for i in range(len(ordem)):
        rows, cols = imgList[ordem[i][1]].tamanho
        limitesAtuais.append(np.float32([[0,0], [0, rows],[cols, rows], [cols, 0]]).reshape(-1, 1, 2))
        pontos1, pontos2 = retornaPontosCoincidentes(imgList[ordem[i][1]], imgList[ordem[i][0]], ordem[i][2], ordem[i][3])
        # matriz de tranformacao eh armazenada em i+1 pois o indice 0 eh referente a primeira imagem (refrencia)
        hList[i+1] = calculaMatrizH(pontos1, pontos2)
        # cada matriz eh multiplicada pela matriz da imagem anterior, para manter uma unica perspectiva
        hList[i+1] = hList[encontraIndiceLocal(ordem[i][0])].dot(hList[i+1])
        limitesFinais.append(cv2.perspectiveTransform(limitesAtuais[i+1], hList[i+1]))

    # confere caso o usuario tenha escolhido a imagem de referencia
    if indice < 0: 
        # descobre a imagem central a partir da posicao em x
        avg_x = np.mean([[x[0][0][0],x[1][0][0],x[2][0][0],x[3][0][0]] for x in limitesFinais],1)
        idx = np.argsort(avg_x)
        idxMeio = math.floor(len(hList)/2)
        indiceMeio = idx[idxMeio]
    else:
        indiceMeio = indice

    limitesFinais.clear() 
    # apos a mudanca de imagem de referencia, os limites finais serao outros

    inversa = np.linalg.inv(hList[indiceMeio])
    # altera a perspectiva do mosaico
    for x in range(qntImgs):
        hList[x] = inversa.dot(hList[x])
        limitesFinais.append(cv2.perspectiveTransform(limitesAtuais[x], hList[x]))

    listaDePontos = np.concatenate(limitesFinais, axis=0)

    [x_min, y_min] = np.int32(listaDePontos.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(listaDePontos.max(axis=0).ravel() + 0.5)

    # translacao necessaria para que nenhuma imagem tenha posicoes negativas
    translation_dist = [-x_min,-y_min] 
    H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])
    hList = [H_translation.dot(hList[x]) for x in range(len(hList))]

    # inicia o panorama com a primeira imagem
    panorama = cv2.warpPerspective(imgList[ordem[0][0]].imagem, hList[0], (x_max-x_min, y_max-y_min))
    # mascara de auxilio para uniao das imagens
    inverseMask = cv2.warpPerspective(np.zeros(imgList[ordem[0][0]].tamanho, dtype='uint8')+255, hList[0], (x_max-x_min, y_max-y_min))
    for i in range(len(ordem)):
        # aplica a matriz de transformacao
        imagemPerspec = cv2.warpPerspective(imgList[ordem[i][1]].imagem, hList[i+1], (x_max-x_min, y_max-y_min))
        # insere a imagem ao mosaico com auxilio da mascara
        panorama = cv2.max(panorama, cv2.bitwise_and(imagemPerspec,imagemPerspec, mask = cv2.bitwise_not(inverseMask)))
        # atualiza a mascara para a proxima insercao
        novaMask = cv2.warpPerspective(np.zeros(imgList[ordem[i][1]].tamanho, dtype='uint8')+255, hList[i+1], (x_max-x_min, y_max-y_min))
        inverseMask = cv2.bitwise_or(inverseMask, novaMask)

    return panorama

def criaMosaicos(fotos, ordens, indicesEscolhidos):
    # gera um mosaico para cada ordem de imagens encontrada
    mosaicos = []
    for i in range(len(ordens)):
        print(f'Restam {len(ordens)-(i)} Mosaicos')
        mosaicos.append(mergeImages(fotos, ordens[i], indicesEscolhidos[i]))
    return mosaicos

def printaOrdens(ordens):
    # exibe os indices de pares de imagens que serao conectados
    for ordem in ordens:
        for x in ordem:
            print(x[:3])
        print(" ")

def descobreNomesOrdem(ordem, fotos):
    # retorna os nomes das imagens utilizadas para determinado mosaico
    nomes = []
    nomes.append(fotos[ordem[0][0]].nome)
    for sequencia in ordem:
        nomes.append(fotos[sequencia[1]].nome)
    return nomes

def is_image(nome):
    # confere se um arquivo e referente a uma imagem
    return nome[-4:].lower() == ".png" or nome[-4:].lower() == ".jpg" or nome[-5:].lower() == ".jpeg"

def filtraImagens(photosNames):
    # retorna apenas os arquivos referentes a imagens
    return list(filter(is_image, photosNames))


if __name__ == "__main__":

    # inicializa variaveis
    folderPath = "./fotos"
    photosPaths=[]
    fotos = []

    print("Carregando...")
    photosNames = os.listdir(folderPath)
    print(photosNames)
    photosNames = filtraImagens(photosNames)

    for name in photosNames:
        imagem = Foto(f'{folderPath}/{name}', name)
        photosPaths.append(f'{folderPath}/{name}')
        fotos.append(imagem)


    print("Fotos carregadas, procurando ordenação...")

    # atualiza o diretorio inicial das janelas de selecao
    diretorio = folderPath

    ordens = encontraOrdem(fotos)
    indicesEscolhidos = [-1 for _ in ordens]

    print("Gerando Mosaicos...")

    mosaicos = criaMosaicos(fotos, ordens, indicesEscolhidos)

    for i in range(len(mosaicos)):
        x = datetime.datetime.now()
        caminho = f'./fotos/{x.strftime("%d%m%Y-%H:%M:%S")}-{i}'
        os.makedirs(caminho)
        cv2.imwrite(caminho+"/mosaico.png", mosaicos[i])
        texto = []
        texto.append(f'O arquivo "mosaico.png" foi confeccionado utilizando as seguintes imagens:\n')
        texto = texto + [nome+'\n' for nome in descobreNomesOrdem(ordens[i], fotos)]
        # o arquivo de texto contem os nomes das imagens utilizadas no mosaico
        with open(caminho+"/imagens_utilizadas.txt", 'w') as arquivoTxt:
            arquivoTxt.writelines(texto)


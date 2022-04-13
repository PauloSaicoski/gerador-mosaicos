import os
import sys
from tkinter import *
from tkinter import filedialog
from PIL import ImageTk,Image
import cv2

import mosaic_generator as mg

PROPORCAO_IMAGENS = 0.2
MAX_IMAGE_SIZE_SELECTOR = 500
MAX_IMAGE_SIZE_MOSAICOS = 900

if __name__ == "__main__":

    # inicializa variaveis
    folderPath = None
    photosPaths=[]
    escolhaInicial = 0
    diretorio = "."
    fotos = []

    # determina a interface grafica inicial
    janelaInicial = Tk()
    janelaInicial.title('Gerador de mosaicos')
    janelaInicial.geometry("300x100")

    def procuraPasta():
        global folderPath
        global escolhaInicial
        global diretorio
        escolhaInicial = 1
        folderPath = filedialog.askdirectory(initialdir=diretorio, title="Escolha a pasta")
        janelaInicial.destroy()

    def procuraImagens():
        global photosPaths
        global escolhaInicial
        global diretorio
        escolhaInicial = 2
        photosPaths = filedialog.askopenfilenames(initialdir=diretorio, title="Escolha as imagens", filetypes=[("Imagem", "*.png *.jpg *.jpeg")])
        janelaInicial.destroy()


    botaoPasta = Button(janelaInicial, text="Escolher Pasta", command = procuraPasta)
    botaoPasta.pack()
    botaoImagens = Button(janelaInicial, text="Escolher Imagens", command=procuraImagens)
    botaoImagens.pack()
    botaoCancela = Button(janelaInicial, text="Cancelar", command=janelaInicial.quit)
    botaoCancela.pack()

    janelaInicial.mainloop()

    if escolhaInicial == 1 and len(folderPath) > 0:
        print("Carregando...")
        photosNames = os.listdir(folderPath)

        photosNames = mg.filtraImagens(photosNames)

        if "Thumbs.db" in photosNames:
            photosNames.remove("Thumbs.db")

        for name in photosNames:
            imagem = mg.Foto(f'{folderPath}/{name}', name)
            photosPaths.append(f'{folderPath}/{name}')
            fotos.append(imagem)

    elif escolhaInicial == 2 and len(photosPaths) > 0:
        print("Carregando...")
        posUltimaBarra = photosPaths[0].rfind("/")
        folderPath = photosPaths[0][:posUltimaBarra]
        for path in photosPaths:
            imagem = mg.Foto(path, path[posUltimaBarra+1:])
            fotos.append(imagem)

    else:
        sys.exit()

    print("Fotos carregadas, procurando ordenação...")

    # atualiza o diretorio inicial das janelas de selecao
    diretorio = folderPath

    ordens = mg.encontraOrdem(fotos)
    indicesEscolhidos = [-1 for _ in ordens]

    janelaOrdens = Tk()
    janelaOrdens.title('Gerador de mosaicos')
    Label(janelaOrdens, text=f'Serão gerados {len(ordens)} mosaicos.\nDeseja escolher a imagem menos\ndistorcida de cada mosaico?').pack()

    def escolherIndice(ordens):
        # alterna para a interface de selecao de imagem de referencia
        janelaOrdens.destroy()

        # funcao baseada nos procedimentos descritos por freeCodeCamp.org

        for i in range(len(ordens)):
            nomeImagens = mg.descobreNomesOrdem(ordens[i],fotos)
            janelaEscolher = Tk()
            janelaEscolher.title('Gerador de mosaicos')

            global imagemAtual
            global my_label
            imagemAtual = 0


            path_list = [f'{folderPath}/{nome}' for nome in nomeImagens]
            image_list = []

            for path in path_list:
                imagem = Image.open(path)
                # determina o tamanho maximo das imagens, mantendo a proporcao
                if imagem.size[0] > MAX_IMAGE_SIZE_SELECTOR or imagem.size[1] > MAX_IMAGE_SIZE_SELECTOR:
                    maior = 0 if imagem.size[0] > imagem.size[1] else 1
                    proporcao = 500/imagem.size[maior]
                    imagem = imagem.resize((round(imagem.size[0]*proporcao),round(imagem.size[1]*proporcao)))
                image_list.append(ImageTk.PhotoImage(imagem))

            my_label = Label(image=image_list[0])
            my_label.grid(row=0, column=0, columnspan=4)

            def forward():
                global my_label
                global imagemAtual
                imagemAtual = (imagemAtual+1)%len(nomeImagens)
                my_label.grid_forget()
                my_label = Label(image=image_list[imagemAtual])
                my_label.grid(row=0, column=0, columnspan=4)

            def back():
                global my_label

                global imagemAtual
                imagemAtual = (imagemAtual-1)%len(nomeImagens)
                my_label.grid_forget()
                my_label = Label(image=image_list[imagemAtual])

                my_label.grid(row=0, column=0, columnspan=4)

            def automatico():
                global imagemAtual
                janelaEscolher.destroy()
                imagemAtual = -1

            button_back = Button(janelaEscolher, text="<<", command=back)
            button_exit = Button(janelaEscolher, text="Escolher esta", command=janelaEscolher.destroy)
            button_forward = Button(janelaEscolher, text=">>", command = forward)
            button_automatico = Button(janelaEscolher, text="Automático", command = automatico)

            button_back.grid(row=1, column=0)
            button_exit.grid(row=1, column=2)
            button_forward.grid(row=1, column=3)
            button_automatico.grid(row = 1, column = 1)

            janelaEscolher.mainloop()

            # retorna o indice da imagem que estava sendo exibida
            indicesEscolhidos[i] = imagemAtual



    botaoEscolher = Button(janelaOrdens, text="Escolher", command = lambda: escolherIndice(ordens))
    botaoEscolher.pack()

    botaoAutomatico = Button(janelaOrdens, text="Automatico", command = janelaOrdens.destroy)
    botaoAutomatico.pack()
    botaoCancela = Button(janelaOrdens, text="Cancelar", command = sys.exit)
    botaoCancela.pack()
    janelaOrdens.mainloop()
    print("Gerando Mosaicos...")

    mosaicos = mg.criaMosaicos(fotos, ordens, indicesEscolhidos)

    def salvar(mosaico, janela, ordem):
        global diretorio
        caminhoMosaico = filedialog.asksaveasfilename(initialdir=diretorio, title="Escolha o local do arquivo", filetypes=[("Imagens", "*.png *.jpg *jpeg")], defaultextension = ".png")
        if(len(caminhoMosaico) == 0):
            return

        posUltimaBarra = caminhoMosaico.rfind("/")
        diretorio = caminhoMosaico[:posUltimaBarra]

        # gera e salva um arquivo de texto com o mesmo nome escolhido pelo usuario
        posExtencao = caminhoMosaico.rfind(".")
        caminhoTxt = caminhoMosaico[:posExtencao] + ".txt"
        texto = []
        nomeMosaico = caminhoMosaico[posUltimaBarra+1:]
        texto.append(f'O mosaico \"{nomeMosaico}\" foi confeccionado utilizando as seguintes imagens:\n')
        texto = texto + [nome+'\n' for nome in mg.descobreNomesOrdem(ordem, fotos)]
        # o arquivo de texto contem os nomes das imagens utilizadas no mosaico
        with open(caminhoTxt, 'w') as arquivoTxt:
            arquivoTxt.writelines(texto)
        janela.destroy()
        cv2.imwrite(caminhoMosaico, mosaico)

    for i in range(len(mosaicos)):
        janelaSalvar = Tk()
        janelaSalvar.title('Gerador de mosaicos')

        # determina o tamanho maximo dos mosaicos exibidos, mantendo a proporcao, sem alterar o arquvivo a ser salvo
        proporcao = 1
        if mosaicos[i].shape[0] > MAX_IMAGE_SIZE_MOSAICOS or mosaicos[i].shape[1] > MAX_IMAGE_SIZE_MOSAICOS:
            maior = 0 if mosaicos[i].shape[0] > mosaicos[i].shape[1] else 1
            proporcao = MAX_IMAGE_SIZE_MOSAICOS/mosaicos[i].shape[maior]

        b,g,r = cv2.split(cv2.resize(mosaicos[i],(0,0), None, proporcao, proporcao))
        img = cv2.merge((r,g,b))
        im = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(im)

        mostraImagem = Label(image=imgtk).grid(row=0, column=0, columnspan=2)
        botaoCancelar = Button(janelaSalvar, text="Cancelar", command=janelaSalvar.destroy).grid(row=1, column=0)
        botaoSalvar = Button(janelaSalvar, text="Salvar", command = lambda: salvar(mosaicos[i], janelaSalvar, ordens[i])).grid(row=1, column=1)

        janelaSalvar.mainloop()

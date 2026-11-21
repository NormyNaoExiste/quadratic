"""
App para deixar imagens quadradas.

Requer: pip install customtkinter pillow
Uso:    python quadrar_app.py
"""

import os, sys

from pathlib import Path
from tkinter import colorchooser, filedialog

import customtkinter as ctk
from PIL import Image, ImageOps

MODOS = {"Cortar": "crop", "Bordas": "pad", "Esticar": "stretch"}
FORMATOS = [("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff")]

def caminho_recurso(rel):
    # funciona tanto rodando o .py quanto dentro do exe
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel)

def quadrar(img, modo="crop", tamanho=None, cor="#ffffff", transparente=False):
    img = ImageOps.exif_transpose(img)  # respeita rotação de fotos de celular
    w, h = img.size
    lado = tamanho or (min(w, h) if modo == "crop" else max(w, h))

    if modo == "crop":
        return ImageOps.fit(img, (lado, lado), Image.LANCZOS, centering=(0.5, 0.5))

    if modo == "stretch":
        return img.resize((lado, lado), Image.LANCZOS)

    img = ImageOps.contain(img, (lado, lado), Image.LANCZOS)
    if transparente:
        fundo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
        img = img.convert("RGBA")
    else:
        fundo = Image.new("RGB", (lado, lado), cor)
        img = img.convert("RGB")
    fundo.paste(img, ((lado - img.width) // 2, (lado - img.height) // 2))
    return fundo


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Quadrar Imagens")
        self.geometry("760x520")
        self.minsize(700, 480)
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        self.iconbitmap(caminho_recurso("icone.ico"))

        self.arquivos = []
        self.cor = "#ffffff"
        self._preview_ref = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._criar_painel()
        self._criar_preview()

    # ---------- interface ----------
    def _criar_painel(self):
        painel = ctk.CTkFrame(self, width=260)
        painel.grid(row=0, column=0, sticky="ns", padx=(16, 8), pady=16)
        painel.grid_propagate(False)

        ctk.CTkButton(painel, text="Escolher imagens", command=self.escolher).pack(
            fill="x", padx=16, pady=(16, 4)
        )
        self.lbl_qtd = ctk.CTkLabel(painel, text="Nenhuma imagem selecionada")
        self.lbl_qtd.pack(padx=16, pady=(0, 12))

        ctk.CTkLabel(painel, text="Modo", anchor="w").pack(fill="x", padx=16)
        self.seg_modo = ctk.CTkSegmentedButton(
            painel, values=list(MODOS), command=self._ao_mudar_modo
        )
        self.seg_modo.set("Cortar")
        self.seg_modo.pack(fill="x", padx=16, pady=(2, 12))

        ctk.CTkLabel(painel, text="Tamanho do lado (px, opcional)", anchor="w").pack(
            fill="x", padx=16
        )
        self.ent_tamanho = ctk.CTkEntry(painel, placeholder_text="ex: 1080")
        self.ent_tamanho.pack(fill="x", padx=16, pady=(2, 12))
        self.ent_tamanho.bind("<KeyRelease>", lambda e: self.atualizar_preview())

        ctk.CTkLabel(painel, text="Cor das bordas", anchor="w").pack(fill="x", padx=16)
        self.btn_cor = ctk.CTkButton(
            painel, text=self.cor, fg_color=self.cor, text_color="gray20",
            hover=False, command=self.escolher_cor,
        )
        self.btn_cor.pack(fill="x", padx=16, pady=(2, 6))
        self.chk_transp = ctk.CTkCheckBox(
            painel, text="Fundo transparente (PNG)", command=self.atualizar_preview
        )
        self.chk_transp.pack(anchor="w", padx=16, pady=(0, 12))

        self.btn_salvar = ctk.CTkButton(
            painel, text="Salvar imagens", command=self.salvar, state="disabled"
        )
        self.btn_salvar.pack(fill="x", padx=16, pady=(8, 4), side="bottom")
        self.barra = ctk.CTkProgressBar(painel)
        self.barra.set(0)
        self.barra.pack(fill="x", padx=16, pady=(0, 4), side="bottom")
        self.lbl_status = ctk.CTkLabel(painel, text="", wraplength=220)
        self.lbl_status.pack(padx=16, side="bottom")

        self._ao_mudar_modo("Cortar")

    def _criar_preview(self):
        area = ctk.CTkFrame(self)
        area.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        area.grid_rowconfigure(0, weight=1)
        area.grid_columnconfigure(0, weight=1)
        self.lbl_preview = ctk.CTkLabel(
            area, text="A prévia aparece aqui", text_color="gray"
        )
        self.lbl_preview.grid(row=0, column=0)

    # ---------- ações ----------
    def _ao_mudar_modo(self, _=None):
        pad = self.seg_modo.get() == "Bordas"
        estado = "normal" if pad else "disabled"
        self.btn_cor.configure(state=estado)
        self.chk_transp.configure(state=estado)
        self.atualizar_preview()

    def escolher(self):
        caminhos = filedialog.askopenfilenames(title="Escolha as imagens", filetypes=FORMATOS)
        if not caminhos:
            return
        self.arquivos = [Path(c) for c in caminhos]
        n = len(self.arquivos)
        self.lbl_qtd.configure(text=f"{n} imagem selecionada" if n == 1 else f"{n} imagens selecionadas")
        self.btn_salvar.configure(state="normal")
        self.barra.set(0)
        self.lbl_status.configure(text="")
        self.atualizar_preview()

    def escolher_cor(self):
        _, hex_cor = colorchooser.askcolor(color=self.cor, title="Cor das bordas")
        if hex_cor:
            self.cor = hex_cor
            self.btn_cor.configure(text=hex_cor, fg_color=hex_cor)
            self.atualizar_preview()

    def _opcoes(self):
        try:
            tamanho = int(self.ent_tamanho.get())
            tamanho = tamanho if tamanho > 0 else None
        except ValueError:
            tamanho = None
        return dict(
            modo=MODOS[self.seg_modo.get()],
            tamanho=tamanho,
            cor=self.cor,
            transparente=bool(self.chk_transp.get()),
        )

    def atualizar_preview(self):
        if not self.arquivos:
            return
        try:
            with Image.open(self.arquivos[0]) as img:
                img.load()
                res = quadrar(img, **self._opcoes())
        except Exception as e:
            self.lbl_preview.configure(image=None, text=f"Erro na prévia:\n{e}")
            return
        res.thumbnail((420, 420))
        self._preview_ref = ctk.CTkImage(res, res, size=res.size)
        self.lbl_preview.configure(image=self._preview_ref, text="")

    def salvar(self):
        pasta = filedialog.askdirectory(title="Onde salvar as imagens quadradas?")
        if not pasta:
            return
        pasta = Path(pasta)
        opcoes = self._opcoes()
        total, ok, erros = len(self.arquivos), 0, []

        for i, arq in enumerate(self.arquivos, 1):
            try:
                with Image.open(arq) as img:
                    res = quadrar(img, **opcoes)
                destino = pasta / arq.name
                contador = 1
                while destino.exists():  # evita sobrescrever
                    destino = pasta / f"{arq.stem}_{contador}{arq.suffix}"
                    contador += 1
                if destino.suffix.lower() in {".jpg", ".jpeg"} and res.mode == "RGBA":
                    fundo = Image.new("RGB", res.size, "white")
                    fundo.paste(res, mask=res.split()[3])
                    res = fundo
                res.save(destino)
                ok += 1
            except Exception as e:
                erros.append(f"{arq.name}: {e}")
            self.barra.set(i / total)
            self.update_idletasks()

        msg = f"{ok} de {total} salvas em:\n{pasta}"
        if erros:
            msg += f"\n{len(erros)} com erro (ex: {erros[0]})"
        self.lbl_status.configure(text=msg)


if __name__ == "__main__":
    App().mainloop()

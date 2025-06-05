import tkinter as tk
from tkinter import scrolledtext, messagebox

from lexer import Lexer, TOKEN_TYPES
from parser import Parser, ParserError

class SyntaxHighlighterApp:
    def __init__(self, master):
        self.master = master
        master.title("Gerçek Zamanlı Sözdizimi Vurgulayıcı")

        self.lexer = Lexer()

        # Ana çerçeve oluştur, satır numaraları ve metin alanını bir arada tutacak
        self.code_frame = tk.Frame(master)
        self.code_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # 1. Satır Numaraları Metin Alanı
        self.line_numbers = tk.Text(self.code_frame,
                                     width=4, 
                                     padx=3,
                                     borderwidth=0, # Kenarlık olmasın
                                     background="#F0F0F0", 
                                     foreground="gray", 
                                     font=("Consolas", 12),
                                     state="disabled", 
                                     wrap="none") 
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # 2. Ana Metin Alanı
        self.text_area = scrolledtext.ScrolledText(self.code_frame,
                                                   wrap=tk.WORD,
                                                   width=80,
                                                   height=30,
                                                   font=("Consolas", 12),
                                                   relief=tk.SUNKEN,
                                                   bd=2,
                                                   bg="#FFFFFF", 
                                                   insertbackground="black") 
        self.text_area.pack(side=tk.RIGHT, expand=True, fill="both")

        self.text_area.config(yscrollcommand=self._on_text_scroll)
        self.line_numbers.config(yscrollcommand=self._on_line_numbers_scroll)



        self.text_area.bind("<KeyRelease>", self.on_key_release)
        self.text_area.bind("<MouseWheel>", self.on_scroll_event)
        self.text_area.bind("<Button-4>", self.on_scroll_event)
        self.text_area.bind("<Button-5>", self.on_scroll_event)
        
        self.define_highlight_tags()

        # Hata mesajı gösterecek bir label
        self.status_label = tk.Label(master,
                                      text="Hazır",
                                      bd=1,
                                      relief=tk.SUNKEN,
                                      anchor=tk.W,
                                      bg="#E0E0E0", 
                                      fg="black")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        self.update_line_numbers()
    
    def _on_text_scroll(self, *args):
        self.line_numbers.yview(*args)
        self.update_line_numbers_scroll_position()

    def _on_line_numbers_scroll(self, *args):
        self.text_area.yview(*args)
        self.update_line_numbers_scroll_position()

    def on_scroll_event(self, event):
        if event.delta: # Windows/Mac
            self.text_area.yview_scroll(int(-1*(event.delta/120)), "units")
        else: # Linux
            if event.num == 4: # Scroll up
                self.text_area.yview_scroll(-1, "units")
            elif event.num == 5: # Scroll down
                self.text_area.yview_scroll(1, "units")
        
        self.update_line_numbers() # Satır numarası içeriğini ve konumunu güncelleyin

    def on_key_release(self, event=None):
        self.update_line_numbers() 
        self.highlight_syntax()
        self.parse_and_report_errors()

    def update_line_numbers(self):
        # Satır numaralarını güncelleme metodu
        self.line_numbers.config(state="normal") # Yazılabilir yap
        self.line_numbers.delete("1.0", tk.END) # Mevcut numaraları sil

        # Metin alanındaki satır sayısını bul
        code_content = self.text_area.get("1.0", tk.END)
        num_lines = code_content.count('\n') + 1
        if not code_content.strip() and num_lines == 1: 
            num_lines = 1 

        # Satır numaralarını ekle
        for i in range(1, num_lines + 1): 
            self.line_numbers.insert(tk.END, f"{i}\n")

        self.line_numbers.config(state="disabled")
        
        self.update_line_numbers_scroll_position()

    def update_line_numbers_scroll_position(self):
        # Satır numaraları ve metin alanının kaydırma pozisyonlarını senkronize et
        # text_area'nın yview pozisyonunu al ve line_numbers'a uygula
        first_visible_line_fraction = self.text_area.yview()[0]
        self.line_numbers.yview_moveto(first_visible_line_fraction)

    def define_highlight_tags(self):
        # Mevcut vurgulama etiketleriniz
        self.text_area.tag_configure("KEYWORD", foreground="blue")
        self.text_area.tag_configure("OPERATOR", foreground="red")
        self.text_area.tag_configure("NUMBER", foreground="purple")
        self.text_area.tag_configure("IDENTIFIER", foreground="black")
        self.text_area.tag_configure("COMMENT", foreground="green", font=("Consolas", 12, "italic"))
        self.text_area.tag_configure("UNKNOWN", foreground="gray", background="yellow")
        self.text_area.tag_configure("ERROR", foreground="white", background="red")
        self.text_area.tag_configure("FLOAT", foreground="orange")
        self.text_area.tag_configure("STRING", foreground="brown")

    def highlight_syntax(self):
        # Önceki tüm vurgulamaları ve hataları temizle
        for tag in self.text_area.tag_names():
            if tag in TOKEN_TYPES or tag == 'UNKNOWN' or tag == 'ERROR':
                self.text_area.tag_remove(tag, "1.0", tk.END)

        code = self.text_area.get("1.0", tk.END)
        tokens = self.lexer.tokenize(code)

        for token in tokens:
            # Token'ın satır bilgisini kontrol et, boş kod durumunda hata olmaması için
            if token.line is None or token.column is None:
                continue # Geçersiz konum bilgisi olan token'ları atla

            start_index = f"{token.line}.{token.column}"
            end_index = f"{token.line}.{token.column + len(token.value)}"

            if token.type in self.text_area.tag_names():
                self.text_area.tag_add(token.type, start_index, end_index)
            elif token.type == 'UNKNOWN':
                self.text_area.tag_add('UNKNOWN', start_index, end_index)

    def parse_and_report_errors(self):
        # Önceki tüm hata vurgulamalarını temizle
        self.text_area.tag_remove("ERROR", "1.0", tk.END)
        self.status_label.config(text="Sözdizimi geçerli.", fg="green")

        code = self.text_area.get("1.0", tk.END)
        tokens = self.lexer.tokenize(code)

        meaningful_tokens = [t for t in tokens if t.type not in ['WHITESPACE', 'COMMENT']]

        parser = Parser(meaningful_tokens)
        try:
            ast = parser.parse()
        except ParserError as e:
            error_message = str(e)
            error_token = e.token

            if error_token:
                start_index = f"{error_token.line}.{error_token.column}"
                end_index = f"{error_token.line}.{error_token.column + len(error_token.value)}"
                self.text_area.tag_add("ERROR", start_index, end_index)

                self.status_label.config(text=f"Sözdizimi Hatası (Satır {error_token.line}, Sütun {error_token.column}): {error_message}", fg="red")
            else:
                self.status_label.config(text=f"Sözdizimi Hatası: {error_message}", fg="red")

# Ana uygulama döngüsü
if __name__ == "__main__":
    root = tk.Tk()
    app = SyntaxHighlighterApp(root)
    root.mainloop()
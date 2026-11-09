from __future__ import annotations

import os
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

from .core import format_date, human_size, list_directory, permission_text


class SlackExplorer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Slack Explorer")
        self.geometry("1180x720")
        self.minsize(820, 500)
        self.option_add("*tearOff", False)

        self.current_path = Path.home()
        self.history: List[Path] = []
        self.history_index = -1
        self.item_paths: Dict[str, Path] = {}
        self.show_hidden = tk.BooleanVar(value=False)
        self.address = tk.StringVar()
        self.search = tk.StringVar()
        self.status = tk.StringVar(value="Pronto")

        self._configure_style()
        self._build_menu()
        self._build_toolbar()
        self._build_content()
        self._build_statusbar()
        self._bind_shortcuts()
        self.navigate(Path.home())

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        available = style.theme_names()
        for preferred in ("clam", "alt", "default"):
            if preferred in available:
                style.theme_use(preferred)
                break
        style.configure("Toolbar.TFrame", background="#f3f5f7")
        style.configure("Treeview", rowheight=27, font=("Sans", 10))
        style.configure("Treeview.Heading", font=("Sans", 10, "bold"))

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu)
        file_menu.add_command(label="Abrir", command=self.open_selected, accelerator="Enter")
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.destroy, accelerator="Ctrl+Q")
        menu.add_cascade(label="Arquivo", menu=file_menu)

        view_menu = tk.Menu(menu)
        view_menu.add_checkbutton(label="Mostrar arquivos ocultos", variable=self.show_hidden,
                                  command=self.refresh, accelerator="Ctrl+H")
        view_menu.add_command(label="Atualizar", command=self.refresh, accelerator="F5")
        menu.add_cascade(label="Exibir", menu=view_menu)

        help_menu = tk.Menu(menu)
        help_menu.add_command(label="Sobre", command=self._show_about)
        menu.add_cascade(label="Ajuda", menu=help_menu)
        self.config(menu=menu)

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, style="Toolbar.TFrame", padding=(8, 7))
        bar.pack(fill="x")
        self.back_button = ttk.Button(bar, text="←", width=3, command=self.go_back)
        self.back_button.pack(side="left", padx=(0, 3))
        self.forward_button = ttk.Button(bar, text="→", width=3, command=self.go_forward)
        self.forward_button.pack(side="left", padx=3)
        ttk.Button(bar, text="↑", width=3, command=self.go_up).pack(side="left", padx=3)
        ttk.Button(bar, text="⌂ Início", command=lambda: self.navigate(Path.home())).pack(side="left", padx=(3, 8))

        address_entry = ttk.Entry(bar, textvariable=self.address)
        address_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        address_entry.bind("<Return>", lambda _event: self.navigate_address())
        ttk.Button(bar, text="Ir", command=self.navigate_address).pack(side="left", padx=(0, 8))

        search_entry = ttk.Entry(bar, textvariable=self.search, width=25)
        search_entry.pack(side="right")
        search_entry.insert(0, "")
        self.search.trace_add("write", lambda *_args: self.refresh())
        ttk.Label(bar, text="Pesquisar:", background="#f3f5f7").pack(side="right", padx=(8, 5))

    def _build_content(self) -> None:
        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True)

        sidebar = ttk.Frame(pane, padding=(8, 8))
        pane.add(sidebar, weight=1)
        ttk.Label(sidebar, text="Locais", font=("Sans", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self.locations = tk.Listbox(sidebar, borderwidth=0, highlightthickness=0,
                                    activestyle="none", font=("Sans", 10), exportselection=False)
        self.locations.pack(fill="both", expand=True)
        self.location_paths: List[Path] = []
        self._populate_locations()
        self.locations.bind("<<ListboxSelect>>", self._location_selected)

        main = ttk.Frame(pane, padding=(0, 8, 8, 8))
        pane.add(main, weight=5)
        columns = ("type", "size", "modified", "permissions")
        self.files = ttk.Treeview(main, columns=columns, show="tree headings", selectmode="extended")
        self.files.heading("#0", text="Nome", anchor="w")
        self.files.heading("type", text="Tipo", anchor="w")
        self.files.heading("size", text="Tamanho", anchor="e")
        self.files.heading("modified", text="Modificado em", anchor="w")
        self.files.heading("permissions", text="Permissões", anchor="w")
        self.files.column("#0", width=330, minwidth=160)
        self.files.column("type", width=210, minwidth=130)
        self.files.column("size", width=95, minwidth=70, anchor="e")
        self.files.column("modified", width=150, minwidth=120)
        self.files.column("permissions", width=105, minwidth=95)
        yscroll = ttk.Scrollbar(main, orient="vertical", command=self.files.yview)
        xscroll = ttk.Scrollbar(main, orient="horizontal", command=self.files.xview)
        self.files.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.files.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        self.files.bind("<Double-1>", lambda _event: self.open_selected())
        self.files.bind("<Return>", lambda _event: self.open_selected())
        self.files.bind("<<TreeviewSelect>>", self._selection_changed)

    def _build_statusbar(self) -> None:
        ttk.Separator(self).pack(fill="x")
        ttk.Label(self, textvariable=self.status, anchor="w", padding=(9, 5)).pack(fill="x")

    def _populate_locations(self) -> None:
        candidates = [
            ("⌂  Pasta pessoal", Path.home()),
            ("▣  Área de trabalho", Path.home() / "Desktop"),
            ("▤  Documentos", Path.home() / "Documentos"),
            ("▧  Downloads", Path.home() / "Downloads"),
            ("▧  Imagens", Path.home() / "Pictures"),
            ("▧  Música", Path.home() / "Music"),
            ("▧  Vídeos", Path.home() / "Videos"),
            ("◉  Sistema de arquivos", Path("/")),
            ("◫  Mídias removíveis", Path("/run/media") / os.environ.get("USER", "")),
        ]
        for label, path in candidates:
            if path.is_dir():
                self.locations.insert("end", label)
                self.location_paths.append(path)

    def _bind_shortcuts(self) -> None:
        self.bind("<Alt-Left>", lambda _event: self.go_back())
        self.bind("<Alt-Right>", lambda _event: self.go_forward())
        self.bind("<Alt-Up>", lambda _event: self.go_up())
        self.bind("<F5>", lambda _event: self.refresh())
        self.bind("<Control-h>", lambda _event: self._toggle_hidden())
        self.bind("<Control-q>", lambda _event: self.destroy())

    def navigate(self, path: Path, add_history: bool = True) -> None:
        path = path.expanduser().absolute()
        if not path.exists():
            messagebox.showerror("Caminho não encontrado", f"A pasta não existe:\n{path}")
            return
        if not path.is_dir():
            self._open_path(path)
            return
        try:
            path.iterdir().__next__()
        except StopIteration:
            pass
        except PermissionError:
            messagebox.showwarning("Acesso negado", f"Seu usuário não tem permissão para abrir:\n{path}")
            return
        except OSError as error:
            messagebox.showerror("Não foi possível abrir", str(error))
            return

        if add_history:
            self.history = self.history[:self.history_index + 1]
            if not self.history or self.history[-1] != path:
                self.history.append(path)
                self.history_index = len(self.history) - 1
        self.current_path = path
        self.address.set(str(path))
        self.search.set("")
        self.refresh()
        self._update_buttons()

    def refresh(self) -> None:
        for item in self.files.get_children():
            self.files.delete(item)
        self.item_paths.clear()
        try:
            entries = list_directory(self.current_path, self.show_hidden.get(), self.search.get())
        except PermissionError:
            self.status.set("Acesso negado")
            return
        except OSError as error:
            self.status.set(f"Erro: {error}")
            return
        for entry in entries:
            icon = "📁" if entry.is_dir else "📄"
            item = self.files.insert("", "end", text=f"{icon}  {entry.name}", values=(
                entry.type_name,
                human_size(entry.size, entry.is_dir),
                format_date(entry.modified),
                permission_text(entry.mode),
            ))
            self.item_paths[item] = entry.path
        label = "item" if len(entries) == 1 else "itens"
        self.status.set(f"{len(entries)} {label}  |  {self.current_path}")

    def navigate_address(self) -> None:
        self.navigate(Path(os.path.expandvars(self.address.get())))

    def go_back(self) -> None:
        if self.history_index > 0:
            self.history_index -= 1
            self.navigate(self.history[self.history_index], add_history=False)

    def go_forward(self) -> None:
        if self.history_index + 1 < len(self.history):
            self.history_index += 1
            self.navigate(self.history[self.history_index], add_history=False)

    def go_up(self) -> None:
        if self.current_path != self.current_path.parent:
            self.navigate(self.current_path.parent)

    def open_selected(self) -> None:
        selection = self.files.selection()
        if not selection:
            return
        path = self.item_paths.get(selection[0])
        if path is None:
            return
        if path.is_dir():
            self.navigate(path)
        else:
            self._open_path(path)

    def _open_path(self, path: Path) -> None:
        try:
            subprocess.Popen(["xdg-open", str(path)], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.status.set(f"Abrindo {path.name}…")
        except OSError as error:
            messagebox.showerror("Não foi possível abrir", str(error))

    def _location_selected(self, _event: object) -> None:
        selected = self.locations.curselection()
        if selected:
            self.navigate(self.location_paths[selected[0]])

    def _selection_changed(self, _event: object) -> None:
        count = len(self.files.selection())
        if count:
            self.status.set(f"{count} selecionado" if count == 1 else f"{count} selecionados")

    def _toggle_hidden(self) -> None:
        self.show_hidden.set(not self.show_hidden.get())
        self.refresh()

    def _update_buttons(self) -> None:
        self.back_button.configure(state="normal" if self.history_index > 0 else "disabled")
        self.forward_button.configure(
            state="normal" if self.history_index + 1 < len(self.history) else "disabled")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "Sobre o Slack Explorer",
            "Slack Explorer 0.1\n\nGerenciador de arquivos leve para Slackware Linux.\n"
            "Esta versão navega e abre arquivos sem funções destrutivas.",
        )


def main() -> None:
    app = SlackExplorer()
    app.mainloop()


if __name__ == "__main__":
    main()

from tkinter import *
from tkinter import ttk
from sys import argv
from os.path import split, splitext
import json


class RobotPreferences(Tk):

    def __init__(self):
        super().__init__()
        self.tool_id: int = 0
        self.account_id = StringVar()
        self.not_loaded_ratio = StringVar()
        self.list_frame = None
        self.canvas = None
        self.tools = []
        self.create_base_gui_elements()
        self.load_robot_parameters(config_filename=self.get_config_filename())

    @staticmethod
    def get_config_filename() -> str:
        """
        Возвращает имя файла конфигурации робота
        @return: имя файла конфигурации робота
        """
        if len(argv) > 1:
            return argv[1]
        else:
            return splitext(split(argv[0])[-1])[0] + '.json'

    def load_robot_parameters(self, config_filename: str) -> dict:
        """
        Возвращает параметры робота в виде dict,list
        @param config_filename: имя файла конфигурации робота в формате json, из которого загружаются настройки
        @return: настройки робота
        """
        with open(config_filename, 'r') as fl:
            res = json.load(fl)
        if 'account' in res:
            self.account_id.set(res['account'])
        if 'not_loaded_ratio' in res:
            self.not_loaded_ratio.set(res['not_loaded_ratio'])
        if 'portfolio' in res and isinstance(res['portfolio'], list):
            for tool in res['portfolio']:
                if 'figi' in tool and 'ratio' in tool:
                    self.add_tool(figi=tool['figi'], ratio=tool['ratio'])
        return res

    def save_robot_parameters(self, config_filename: str = ''):
        """
        Сохраняет параметры в файл
        @return: None
        """
        if config_filename == '':
            config_filename = self.get_config_filename()
        parameters = {
            "account": self.account_id.get(),
            "not_loaded_ratio": self.not_loaded_ratio.get(),
            "portfolio": []
        }
        for item in self.tools:
            if item['figi'].get() != '' and item['ratio'].get() != '':
                parameters['portfolio'].append({'figi': item['figi'].get(), 'ratio': item['ratio'].get()})

        with open(config_filename, 'w', encoding='utf-8') as f:
            json.dump(parameters, f, ensure_ascii=False, indent=4)

    def _get_new_tool_id(self):
        """
        Возвращает идентификатор инструмента, уникальный в рамках текущего запуска программы
        :return: новый идентификатор инструмента
        """
        self.tool_id += 1
        return self.tool_id

    def add_tool(self, figi: str = '', ratio: str = '') -> None:
        """
        Добавляет строку в список инструментов
        @return: None
        """
        for item in self.tools:
            if item['figi'].get() == figi:
                i = 1
                for child in item['frame'].winfo_children():
                    if i > 1:
                        child.focus_set()
                        break
                    else:
                        i += 1
                return

        new_frame = ttk.Frame(self.canvas, padding="3 3 3 3")

        tool_variable = {'figi': StringVar(value=figi),
                         'ratio': StringVar(value=ratio),
                         'frame': new_frame,
                         'id': self._get_new_tool_id()}
        self.tools.append(tool_variable)
        next_line = len(self.list_frame.winfo_children())
        new_frame.grid(column=1, row=next_line, sticky=(W, E))
        new_frame.config()
        ttk.Label(new_frame, text='FIGI').grid(column=1, row=1, sticky=(W, E))
        ttk.Entry(new_frame, width=15, textvariable=tool_variable['figi']).grid(column=2, row=1, sticky=(W, E))
        ttk.Label(new_frame, text='Вес инструмента').grid(column=3, row=1, sticky=(W, E))
        ttk.Entry(new_frame, width=10, textvariable=tool_variable['ratio']).grid(column=4, row=1, sticky=(W, E))
        ttk.Button(new_frame, text="X", width=2, command=lambda f=tool_variable['id']: self.delete_tool(f)).grid(column=5, row=1, sticky=W)

    def delete_tool(self, item_id: int = None):
        """
        Удаляет строку, соответствующую инструменту (обработчик события нажатия кнопки с крестом в строке инструмента)
        :return: None
        """
        for item in self.tools:
            if item['id'] == item_id:
                for child in item['frame'].winfo_children():
                    child.destroy()
                item['frame'].destroy()
                self.tools.remove(item)
                line = 0
                # Перепозиционировать оставшиеся фреймы
                for child in self.list_frame.winfo_children():
                    child.grid(row=line)
                    line += 1
                break

    def create_base_gui_elements(self):
        """
        Создает базовые элементы интерфейса
        @return: None
        """
        self.title('Конфигурация индексного робота')
        # TODO:
        main_frame = ttk.Frame(self, padding="5 5 5 5")
        main_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        ttk.Label(main_frame, text='Идентификатор счета (account_id)').grid(column=1, row=1, sticky=(W, E))
        ttk.Entry(main_frame, width=14, textvariable=self.account_id).grid(column=2, row=1, sticky=(W, E))
        ttk.Label(main_frame, text='Незагруженная доля средств счета').grid(column=1, row=2, sticky=(W, E))
        ttk.Entry(main_frame, width=14, textvariable=self.not_loaded_ratio).grid(column=2, row=2, sticky=(W, E))

        self.list_frame = ttk.Frame(main_frame, padding="0 20 0 20")
        self.list_frame.grid(column=1, row=3, sticky=(N, W, E, S), columnspan=5)

        sb_ver = ttk.Scrollbar(self.list_frame, orient=VERTICAL)
        sb_ver.pack(fill=Y, side=RIGHT, expand=FALSE)
        self.canvas = Canvas(self.list_frame, bd=0, highlightthickness=0,
                             yscrollcommand=sb_ver.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        sb_ver.config(command=self.canvas.yview)

        ttk.Button(main_frame,
                   text="Добавить инструмент",
                   command=self.add_tool).grid(column=1, row=4, sticky=W)
        ttk.Button(main_frame,
                   text="Сохранить параметры",
                   command=self.save_robot_parameters).grid(column=2, row=4, sticky=W)

        # TODO: Убрать временные команды
        # for item, value in ttk.Button().configure().items():
        #     print(item, value)
        #     if item == 'style':
        #         for item2 in value:
        #             print(' ' * 5, item2)


gui: RobotPreferences = RobotPreferences()
gui.mainloop()


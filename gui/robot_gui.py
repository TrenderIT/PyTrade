from tkinter import *
from tkinter import ttk
from sys import argv
from os.path import split, splitext
import json


class RobotPreferences(Tk):

    def __init__(self):
        super().__init__()
        self.account_id = StringVar()
        self.list_frame = None
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
        # TODO:
        print(self.tools)
        pass

    def add_tool(self, figi: str = '', ratio: str = '') -> None:
        """
        Добавляет строку в список инструментов
        @return: None
        """
        new_frame = ttk.Frame(self, padding="3 3 12 12")
        self.tools.append({'figi': StringVar(value=figi), 'ratio': StringVar(value=ratio)})
        next_line = len(self.list_frame.winfo_children()) % 3 + 1
        # ttk.Label(self.list_frame, )

        # TODO:
        pass

    def create_base_gui_elements(self):
        """
        Создает базовые элементы интерфейса
        @return: None
        """
        # TODO:
        self.title('Конфигурация индексного робота')
        main_frame = ttk.Frame(self, padding="3 3 12 12")
        main_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        ttk.Label(main_frame, text='Идентификатор счета (account_id)').grid(column=1, row=1, sticky=(W, E))
        ttk.Entry(main_frame, width=10, textvariable=self.account_id).grid(column=2, row=1, sticky=(W, E))
        self.list_frame = ttk.Frame(main_frame, padding="3 3 12 12")
        self.list_frame.grid(column=1, row=2, sticky=(N, W, E, S), columnspan=3)
        ttk.Button(main_frame,
                   text="Добавить инструмент",
                   command=self.add_tool).grid(column=1, row=3, sticky=W)
        ttk.Button(main_frame,
                   text="Сохранить параметры",
                   command=self.save_robot_parameters).grid(column=2, row=3, sticky=W)


gui: RobotPreferences = RobotPreferences()
gui.mainloop()


import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window

API_URL = "http://127.0.0.1:8000"  # Якщо ти на Android — зміни на локальну IP FastAPI-сервера

Window.clearcolor = (30/255, 42/255, 56/255, 1)  # Змінюємо колір фону вікна

class BookList(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.load_books()

    def load_books(self):
        try:
            response = requests.get(f"{API_URL}/api/books")
            books = response.json()
            for book in books:
                btn = Button(
                    text=f"{book['title']} — {book['author']}",
                    size_hint_y=1,
                    height=100
                )
                btn.bind(on_press=lambda instance, b=book: self.show_book_detail(b))
                self.add_widget(btn)
        except Exception as e:
            self.add_widget(Label(text="Помилка завантаження"))

    def show_book_detail(self, book):
        self.clear_widgets()
        #boox = BoxLayout(orientation='vertical', size_hint_y=1)
        
        self.add_widget(Label(text=f"{book['title']} -  {book['author']}", font_size=20))
        #box = BoxLayout(orientation='horizontal', size_hint_y=1)
        self.add_widget(Label(text=f"Опис: {book['description']}", font_size = 20, text_size=(900, None),size_hint_y=None, height=300 ))

        # Зображення
        image_url = f"{API_URL}/image/{book['id']}"
        self.add_widget(AsyncImage(source=image_url, size_hint_y=None, height=300))
        #self.add_widget(box)
        #boox.add_widget(box)


        # Назад
        self.add_widget(Button(text="Назад", on_press=lambda x: self.reset()))
        #self.add_widget(boox)

    def reset(self):
        self.clear_widgets()
        self.load_books()


    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

class MainApp(App):
    def build(self):
        root = ScrollView()
        box = BookList(size_hint_y=1)
        box.bind(minimum_height=box.setter('height'))
        root.add_widget(box)
        return root

if __name__ == "__main__":
    MainApp().run()
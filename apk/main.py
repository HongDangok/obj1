from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.modalview import ModalView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from datetime import datetime, date, timedelta, time
from functools import partial
from plyer import notification

class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 1, 0, 1)  # Background color
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[20])
            self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class NoteApp(App):
    def build(self):
        self.store = JsonStore('notes.json')
        self.layout = RelativeLayout()

        # Tạo một BoxLayout cho các nút ở góc dưới bên trái
        self.button_layout = BoxLayout(size_hint=(None, None), size=(300, 50), pos_hint={'x': 0.05, 'y': 0.05})

        # Nút để thêm ghi chú mới
        self.add_note_button = RoundedButton(text='+', size_hint=(None, None), size=(50, 50))
        self.add_note_button.bind(on_press=self.show_add_note_popup)
        self.button_layout.add_widget(self.add_note_button)

        # Nút để xóa các ghi chú đã chọn
        self.delete_note_button = RoundedButton(text='-', size_hint=(None, None), size=(50, 50))
        self.delete_note_button.bind(on_press=self.toggle_delete_mode)
        self.button_layout.add_widget(self.delete_note_button)

        # Nút tìm kiếm
        self.search_button = RoundedButton(text='Tìm', size_hint=(None, None), size=(50, 50))
        self.search_button.bind(on_press=self.search_notes_button)
        self.button_layout.add_widget(self.search_button)

        # Nút xem lịch
        self.calendar_button = RoundedButton(text='Lịch', size_hint=(None, None), size=(50, 50))
        self.calendar_button.bind(on_press=self.show_calendar_popup)
        self.button_layout.add_widget(self.calendar_button)

        self.layout.add_widget(self.button_layout)

        # Thêm thanh tìm kiếm
        self.search_input = TextInput(size_hint=(0.7, None), height=40, pos_hint={'x': 0.15, 'y': 0.95}, hint_text='Tìm kiếm ghi chú...')
        self.layout.add_widget(self.search_input)

        # ScrollView để hiển thị danh sách ghi chú
        self.note_list = ScrollView(size_hint=(1, None), size=(self.layout.width, 500), pos_hint={'top': 0.9})
        self.note_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.note_layout.bind(minimum_height=self.note_layout.setter('height'))
        self.note_list.add_widget(self.note_layout)
        self.layout.add_widget(self.note_list)

        self.delete_mode = False
        self.selected_note_keys = []

        self.load_notes()
        return self.layout

    def show_add_note_popup(self, instance, date_str=None):
        # Popup để thêm ghi chú mới
        self.popup_layout = BoxLayout(orientation='vertical', padding=10)
        self.note_title_input = TextInput(hint_text='Tiêu đề', size_hint_y=None, height=40)
        self.note_content_input = TextInput(hint_text='Nội dung', size_hint_y=None, height=100)
        self.note_date_input = TextInput(hint_text='Ngày (YYYY-MM-DD)', size_hint_y=None, height=40, text=date_str if date_str else '')
        self.note_time_input = TextInput(hint_text='Giờ nhắc (HH:MM)', size_hint_y=None, height=40)
        self.save_button = Button(text='Lưu', size_hint_y=None, height=50)
        self.save_button.bind(on_press=self.add_note)
        self.popup_layout.add_widget(self.note_title_input)
        self.popup_layout.add_widget(self.note_content_input)
        self.popup_layout.add_widget(self.note_date_input)
        self.popup_layout.add_widget(self.note_time_input)
        self.popup_layout.add_widget(self.save_button)

        self.popup = Popup(title='Thêm ghi chú', content=self.popup_layout, size_hint=(0.8, 0.8))
        with self.popup.canvas.before:
            Color(1, 1, 1, 1)
            self.popup_rect = RoundedRectangle(size=self.popup.size, pos=self.popup.pos, radius=[20])
            self.popup.bind(pos=self.update_popup_rect, size=self.update_popup_rect)
        self.popup.open()

    def update_popup_rect(self, *args):
        self.popup_rect.pos = self.popup.pos
        self.popup_rect.size = self.popup.size

    def add_note(self, instance):
        title = self.note_title_input.text
        content = self.note_content_input.text
        date_str = self.note_date_input.text
        time_str = self.note_time_input.text

        if title and content and date_str and time_str:
            try:
                note_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            except ValueError:
                self.show_error_popup('Định dạng ngày giờ không hợp lệ. Vui lòng nhập theo định dạng YYYY-MM-DD HH:MM.')
                return

            key = str(int(time.time()))
            self.store.put(key, title=title, content=content, datetime=note_datetime.strftime('%Y-%m-%d %H:%M'))

            # Lên lịch nhắc nhở
            Clock.schedule_once(partial(self.trigger_alarm, key), (note_datetime - datetime.now()).total_seconds())
            self.popup.dismiss()
            self.load_notes()
        else:
            self.show_error_popup('Vui lòng nhập đầy đủ thông tin.')

    def show_error_popup(self, message):
        error_popup = Popup(title='Lỗi', content=Label(text=message), size_hint=(0.8, 0.2))
        with error_popup.canvas.before:
            Color(1, 1, 1, 1)
            self.error_popup_rect = RoundedRectangle(size=error_popup.size, pos=error_popup.pos, radius=[20])
            error_popup.bind(pos=self.update_error_popup_rect, size=self.update_error_popup_rect)
        error_popup.open()

    def update_error_popup_rect(self, *args):
        self.error_popup_rect.pos = self.popup.pos
        self.error_popup_rect.size = self.popup.size

    def load_notes(self):
        self.note_layout.clear_widgets()
        for key in self.store:
            note = self.store[key]
            note_label = LongPressButton(text=f"{note['title']} - {note['datetime']}", size_hint_y=None, height=40)
            note_label.bind(on_release=lambda instance, key=key: self.show_note_details(key))
            note_label.bind(on_long_press=lambda instance, key=key: self.select_note_for_deletion(key))
            self.note_layout.add_widget(note_label)

    def show_note_details(self, key):
        note = self.store[key]
        detail_popup = Popup(title=note['title'], content=Label(text=note['content']), size_hint=(0.8, 0.8))
        with detail_popup.canvas.before:
            Color(1, 1, 1, 1)
            self.detail_popup_rect = RoundedRectangle(size=detail_popup.size, pos=detail_popup.pos, radius=[20])
            detail_popup.bind(pos=self.update_detail_popup_rect, size=self.update_detail_popup_rect)
        detail_popup.open()

    def update_detail_popup_rect(self, *args):
        self.detail_popup_rect.pos = self.popup.pos
        self.detail_popup_rect.size = self.popup.size

    def select_note_for_deletion(self, key):
        if self.delete_mode:
            if key in self.selected_note_keys:
                self.selected_note_keys.remove(key)
            else:
                self.selected_note_keys.append(key)

    def toggle_delete_mode(self, instance):
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            self.show_delete_confirmation_popup()
        else:
            self.selected_note_keys = []
            self.load_notes()

    def show_delete_confirmation_popup(self):
        if self.selected_note_keys:
            delete_popup = ModalView(size_hint=(0.5, 0.5))
            content = BoxLayout(orientation='vertical')
            delete_label = Label(text='Bạn có chắc muốn xóa các ghi chú này?')
            delete_button = Button(text='Xóa')
            delete_button.bind(on_press=self.delete_notes)
            content.add_widget(delete_label)
            content.add_widget(delete_button)
            delete_popup.add_widget(content)
            with delete_popup.canvas.before:
                Color(1, 1, 1, 1)
                self.delete_popup_rect = RoundedRectangle(size=delete_popup.size, pos=delete_popup.pos, radius=[20])
                delete_popup.bind(pos=self.update_delete_popup_rect, size=self.update_delete_popup_rect)
            delete_popup.open()

    def update_delete_popup_rect(self, *args):
        self.delete_popup_rect.pos = self.popup.pos
        self.delete_popup_rect.size = self.popup.size

    def delete_notes(self, instance):
        for key in self.selected_note_keys:
            self.store.delete(key)
        self.selected_note_keys = []
        self.load_notes()

    def search_notes(self, instance, text):
        self.note_layout.clear_widgets()
        for key in self.store:
            note = self.store[key]
            if text.lower() in note['title'].lower() or text.lower() in note['content'].lower():
                note_label = LongPressButton(text=f"{note['title']} - {note['datetime']}", size_hint_y=None, height=40)
                note_label.bind(on_release=lambda instance, key=key: self.show_note_details(key))
                note_label.bind(on_long_press=lambda instance, key=key: self.select_note_for_deletion(key))
                self.note_layout.add_widget(note_label)

    def search_notes_button(self, instance):
        search_text = self.search_input.text
        self.search_notes(instance, search_text)

    def show_calendar_popup(self, instance):
        self.calendar_popup_layout = BoxLayout(orientation='vertical', padding=10)
        self.calendar_label = Label(text=str(date.today()), size_hint_y=None, height=40)
        self.prev_day_button = Button(text='<', size_hint_y=None, height=40)
        self.next_day_button = Button(text='>', size_hint_y=None, height=40)
        self.prev_day_button.bind(on_press=self.prev_day)
        self.next_day_button.bind(on_press=self.next_day)

        self.select_date_button = Button(text='Chọn ngày', size_hint_y=None, height=50)
        self.select_date_button.bind(on_press=self.select_date)

        button_layout = BoxLayout(size_hint_y=None, height=40)
        button_layout.add_widget(self.prev_day_button)
        button_layout.add_widget(self.calendar_label)
        button_layout.add_widget(self.next_day_button)

        self.calendar_popup_layout.add_widget(button_layout)
        self.calendar_popup_layout.add_widget(self.select_date_button)

        self.calendar_popup = Popup(title='Chọn ngày', content=self.calendar_popup_layout, size_hint=(0.8, 0.8))
        with self.calendar_popup.canvas.before:
            Color(1, 1, 1, 1)
            self.calendar_popup_rect = RoundedRectangle(size=self.calendar_popup.size, pos=self.calendar_popup.pos, radius=[20])
            self.calendar_popup.bind(pos=self.update_calendar_popup_rect, size=self.update_calendar_popup_rect)
        self.calendar_popup.open()

    def update_calendar_popup_rect(self, *args):
        self.calendar_popup_rect.pos = self.calendar_popup.pos
        self.calendar_popup_rect.size = self.calendar_popup.size

    def prev_day(self, instance):
        current_date = datetime.strptime(self.calendar_label.text, '%Y-%m-%d').date()
        prev_date = current_date - timedelta(days=1)
        self.calendar_label.text = str(prev_date)

    def next_day(self, instance):
        current_date = datetime.strptime(self.calendar_label.text, '%Y-%m-%d').date()
        next_date = current_date + timedelta(days=1)
        self.calendar_label.text = str(next_date)

    def select_date(self, instance):
        selected_date = self.calendar_label.text
        self.calendar_popup.dismiss()
        self.show_add_note_popup(instance, date_str=selected_date)

    def trigger_alarm(self, key, dt):
        note = self.store[key]
        notification.notify(
            title='Ghi chú nhắc nhở',
            message=f"{note['title']} - {note['datetime']}\nNội dung: {note['content']}",
            timeout=10
        )
        self.store.delete(key)
        self.load_notes()

class LongPressButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.long_press_event = None

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            self.long_press_event = Clock.schedule_once(self.on_long_press, 1)
            return True
        return False

    def on_touch_up(self, touch):
        if self.long_press_event:
            self.long_press_event.cancel()
            self.long_press_event = None
        return super().on_touch_up(touch)

    def on_long_press(self, dt):
        self.dispatch('on_long_press')

    def on_long_press(self):
        pass

if __name__ == '__main__':
    NoteApp().run()
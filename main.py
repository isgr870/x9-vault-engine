import threading
import time
import os
import sys

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from jnius import autoclass, PythonJavaClass, java_method

PythonActivity = autoclass('org.kivy.android.PythonActivity')
WebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
WebSettings = autoclass('android.webkit.WebSettings')

class Runnable(PythonJavaClass):
    __javainterfaces__ = ['java/lang/Runnable']

    def __init__(self, func):
        super().__init__()
        self.func = func

    @java_method('()V')
    def run(self):
        self.func()

class X9App(App):
    def build(self):
        self.server_thread = threading.Thread(target=self.run_x9_server, daemon=True)
        self.server_thread.start()

        activity = PythonActivity.mActivity
        self.webview = WebView(activity)
        
        settings = self.webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        
        self.webview.setWebViewClient(WebViewClient())
        
        threading.Thread(target=self.load_dashboard, daemon=True).start()
        return BoxLayout()

    def load_dashboard(self):
        time.sleep(1.5)
        activity = PythonActivity.mActivity
        activity.runOnUiThread(Runnable(lambda: self.webview.loadUrl("http://127.0.0.1:8090/")))

    def run_x9_server(self):
        import x9_unified
        if hasattr(x9_unified, 'run_server'):
            x9_unified.run_server()

if __name__ == '__main__':
    X9App().run()

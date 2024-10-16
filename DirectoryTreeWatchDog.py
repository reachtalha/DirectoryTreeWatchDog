from textual import on
from textual.app import App, ComposeResult
from textual.message import Message
from textual.widgets import DirectoryTree, Footer, Header, RichLog
from textual.worker import Worker
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class FSEHandler(FileSystemEventHandler):
    class FileSystemChangeMessage(Message):
        """ A Notification of a change to a directory"""

        def __init__(self, event_type: str, is_directory: bool, src_path: str, dst_path: str = None):
            super().__init__()
            self.event_type: str = event_type
            self.is_directory: bool = is_directory
            self.src_path: str = src_path
            self.dst_path: str = dst_path

    class Info(Message):
        """ A Notification of a change to a directory"""

        def __init__(self, func: str, msg: str):
            super().__init__()
            self.func: str = func
            self.msg: str = msg

    def __init__(self, app: App) -> None:
        super().__init__()
        self.app = app

    def on_any_event(self, event):
        match event.event_type:
            case 'opened' | 'closed':
                pass

            case 'moved' | 'created' | 'modified' | 'deleted':
                self.app.post_message(
                    FSEHandler.FileSystemChangeMessage(
                        event.event_type,
                        event.is_directory,
                        event.src_path,
                        getattr(event, "dest_path", "")
                    )
                )

            case _:
                self.app.post_message(
                    FSEHandler.Info("on_any_event",
                                    f"[cyan]event_Type={event.event_type}, "
                                    f"is_dir={event.is_directory}, "
                                    f"src_path={event.src_path}, "
                                    f"dst_path={getattr(event, 'dest_path', '')}[/]"
                                    )
                )


class TestThreadApp(App):
    BINDINGS = [
        ('d', 'toggle_dark', "Toggle dark mode"),
        ('q', 'quit', "Quit Application"),
    ]

    watchDirectory = "./"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        self.dt = DirectoryTree(self.watchDirectory)
        self.dt.styles.border = ("round", "green")
        self.dt.styles.height = "4fr"
        self.dt.border_title = "Directory Tree"
        yield self.dt
        self.logger = RichLog(markup=True)
        self.logger.border_title = "Message Log"
        self.logger.styles.border = ("round", "green")
        self.logger.styles.height = "4fr"
        yield self.logger

    @on(FSEHandler.FileSystemChangeMessage)
    def fs_change(self, fs: FSEHandler.FileSystemChangeMessage):
        match fs.event_type:
            case 'created':
                pass

            case 'deleted':
                pass

            case 'moved':
                pass

            case 'modified':
                if fs.is_directory:
                    anode = self.dt.root
                    for child_label in fs.src_path.split('/')[1:]:
                        for child in anode.children:
                            if child.label == child_label:
                                anode = child
                    self.dt.reload_node(anode)

        self.logger.write(f"{'fs_change':>15}:[cyan]event_type={fs.event_type}, "
                          f"is_directory={fs.is_directory}, "
                          f"src_path={fs.src_path}, "
                          f"dst_path={fs.dst_path}[/]"
                          )

    @on(FSEHandler.Info)
    def log_info(self, msg: FSEHandler.Info):
        self.logger.write(f"{msg.func:>15}:{msg.msg}")
        return

    async def on_mount(self) -> None:
        self.query_one(DirectoryTree).root.expand_all()  # Load all the items so that we can access Them when needed
        self.observer = Observer()
        self.event_handler = FSEHandler(self)  # Pass the watchdog_screen instance
        self.observer.schedule(self.event_handler, self.watchDirectory, recursive=True)
        t = Worker(self, self.observer.start(), name="WatchDog", description="Separate Thread running WatchDog",
                   thread=True)
        self.workers.add_worker(t, start=False, exclusive=True)


if __name__ == "__main__":
    my_app = TestThreadApp()
    my_app.run()

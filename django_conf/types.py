class Secret(str):
    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}('**********')"

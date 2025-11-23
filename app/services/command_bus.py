# Simple in-memory command bus for demonstration. 
# In a production environment with multiple workers, use Redis or a DB table.

class CommandBus:
    _commands = {}

    @classmethod
    def add_command(cls, feeder_id, command):
        if feeder_id not in cls._commands:
            cls._commands[feeder_id] = []
        cls._commands[feeder_id].append(command)

    @classmethod
    def get_commands(cls, feeder_id):
        if feeder_id in cls._commands and cls._commands[feeder_id]:
            # Return all pending commands and clear the list
            cmds = cls._commands[feeder_id]
            cls._commands[feeder_id] = []
            return cmds
        return []

    @classmethod
    def has_commands(cls, feeder_id):
        return feeder_id in cls._commands and len(cls._commands[feeder_id]) > 0

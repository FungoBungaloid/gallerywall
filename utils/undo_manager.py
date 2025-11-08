"""
Undo/Redo Management System
"""
from typing import List, Callable, Any
from dataclasses import dataclass


@dataclass
class Command:
    """Represents an undoable/redoable command"""
    name: str
    undo_func: Callable
    redo_func: Callable
    undo_data: Any = None
    redo_data: Any = None


class UndoManager:
    """Manages undo/redo operations"""

    def __init__(self, max_history: int = 50):
        """
        Initialize undo manager

        Args:
            max_history: Maximum number of commands to keep in history
        """
        self.max_history = max_history
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []

    def execute(self, command: Command):
        """
        Execute a command and add it to undo history

        Args:
            command: Command to execute
        """
        # Execute the redo function (do the action)
        command.redo_func(command.redo_data)

        # Add to undo stack
        self.undo_stack.append(command)

        # Limit stack size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        # Clear redo stack when new action is performed
        self.redo_stack.clear()

    def undo(self) -> bool:
        """
        Undo the last command

        Returns:
            True if undo was successful, False if nothing to undo
        """
        if not self.can_undo():
            return False

        command = self.undo_stack.pop()
        command.undo_func(command.undo_data)
        self.redo_stack.append(command)

        return True

    def redo(self) -> bool:
        """
        Redo the last undone command

        Returns:
            True if redo was successful, False if nothing to redo
        """
        if not self.can_redo():
            return False

        command = self.redo_stack.pop()
        command.redo_func(command.redo_data)
        self.undo_stack.append(command)

        return True

    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return len(self.redo_stack) > 0

    def get_undo_description(self) -> str:
        """Get description of action that would be undone"""
        if self.can_undo():
            return self.undo_stack[-1].name
        return ""

    def get_redo_description(self) -> str:
        """Get description of action that would be redone"""
        if self.can_redo():
            return self.redo_stack[-1].name
        return ""

    def clear(self):
        """Clear all undo/redo history"""
        self.undo_stack.clear()
        self.redo_stack.clear()

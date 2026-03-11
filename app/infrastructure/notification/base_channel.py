from abc import ABC, abstractmethod

class BaseNotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send(self, message: str, **kwargs) -> str:
        """
        Send a notification message.
        Returns a success/failure message string.
        """
        raise NotImplementedError

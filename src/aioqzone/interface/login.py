from abc import ABC, abstractmethod, abstractproperty


class Loginable(ABC):
    @abstractproperty
    def gtk(self) -> int:
        """Get gtk in any way. Allow cached result.

        Returns:
            int: gtk. Cached gtk is preferable.
        """
        return self.new_gtk()

    @abstractmethod
    def new_gtk(self) -> int:
        """Get a new gtk. Means, cached gtk is not allowed.

        Returns:
            int: gtk. Shouldn't be a cached one.
        """
        return 0

    @abstractproperty
    def uin(self) -> int:
        return 0

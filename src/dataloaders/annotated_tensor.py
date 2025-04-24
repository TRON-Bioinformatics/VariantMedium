from typing import Text, Tuple


class AnnotatedTensor:
    """Encapsulate all information necessary for training and evaluating for one variant."""

    def __init__(
            self,
            tensor: Text,
            variant: int,
            length: int,
            metadata: Tuple[Text, int, Text, Text, Text, Text, int],
            clip_length: int,
    ):
        """Initialize the annotated tensor object.

        :param tensor: Path to the tensor.
        :param variant: Type of variant, one of 0,1,2,3
        :param length: Type of variant length, one of 0,1,2,3
        :param metadata: Tuple including chromosome, position, ref, alt, sample name, clipping
        :param clip_length: How much of the tensor should be zeroed out (for data augmentatıion).
        """
        self.tensor = tensor
        self.mutation_type = int(variant)
        self.mutation_length_type = int(length)
        self.metadata = metadata
        self.clip_length = clip_length

    def __repr__(self) -> Text:
        """Override the default __repr__ implementation."""
        return '{} {} {} {}'.format(
            self.tensor,
            self.mutation_type,
            self.mutation_length_type,
            self.metadata
        )

    def __eq__(self, other) -> bool:
        """Override the default __eq__ implementation.

        :param other: Object that self is being compared to.
        :return: True if the contents of the objects match, False otherwise.
        """
        if isinstance(other, AnnotatedTensor):
            return self.tensor == other.tensor \
                   and self.mutation_type == other.mutation_type \
                   and self.mutation_length_type == other.mutation_length_type \
                   and self.metadata == other.metadata
        return False

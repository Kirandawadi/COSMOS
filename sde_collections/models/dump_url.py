from .url import Url


class DumpUrl(Url):
    """Model for storing all the imported URLs before seperating them into delta URLs and Curated URLs."""

    class Meta:
        verbose_name = "Dump URL"
        verbose_name_plural = "Dump URLs"

    def save(self, *args, **kwargs):
        if not self.pk:  # Ensure it's only called on create
            super().save(*args, **kwargs)  # Save the parent `Url` entry
        super().save(*args, **kwargs)

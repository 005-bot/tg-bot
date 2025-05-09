import logging

from address_parser import AddressParser

from app.services.storage import Storage

logger = logging.getLogger(__name__)


class Migrator:
    # Minimum confidence threshold for accepting an address match during migration
    MATCH_CONFIDENCE_THRESHOLD = 0.60

    def __init__(self, storage: Storage):
        """
        Initialize the Migrator.

        :param storage: An instance of the Storage class used for migration operations.
        """

        self.version = 1
        self.storage = storage

    async def migrate(self):
        """
        Run all available migrations.

        :return: None
        """

        version = await self.storage.get_version()
        if version >= self.version:
            return

        logger.info("Starting migration from version %d to %d", version, self.version)
        await self.storage.migrate()

        if version < 1:
            filters = await self.storage.get_subscribed()
            async with AddressParser() as parser:
                count = 0
                for user_id, filter in filters.items():
                    if not filter.street:
                        continue

                    parsed = await parser.normalize(filter.street)
                    if (
                        not parsed
                        or parsed.confidence < self.MATCH_CONFIDENCE_THRESHOLD
                    ):
                        continue

                    await self.storage.subscribe(user_id, parsed.normalized_name)
                    count += 1

                logger.info("Updated %d subscriptions", count)

        logger.info("Migration complete")
        await self.storage.set_version(self.version)

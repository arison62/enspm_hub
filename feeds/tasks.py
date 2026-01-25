import logging
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task
from feeds.services.score_service import ScoreCalculator

logger = logging.getLogger(__name__)

@db_periodic_task(crontab(minute='*/30'))
def task_update_all_feed_scores():
    """
     Taches peridoque s'executant toutes les 15 minutes pour rafraichir
     les scores des profils et des posts actifs
    """
    logger.info("STARTING PERIODIC SCORE RECALCULATION...")
    try:
        # On remonte sur 24h d'activité par défaut
        stats = ScoreCalculator.batch_update_scores(hours_back=24)
        
        logger.info(
            f"Score recalculation completed successfully. "
            f"Updated {stats['profils_updated']} profiles and {stats['posts_updated']} posts.",
            extra={
                'profils_count': stats['profils_updated'],
                'posts_count': stats['posts_updated']
            }
        )
    except Exception as e:
        logger.error(
            f"Critical error during periodic score update: {str(e)}",
            exc_info=True
        )
    
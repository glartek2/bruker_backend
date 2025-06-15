from django.db.models import Q
from rest_framework.filters import BaseFilterBackend
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DynamicJsonFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):

        q = Q()

        reserved = {
            'page', 'page_size', 'pagination', 'ordering', 'search', 'id', 'room_number', 'capacity',
            'equipment__details', 'equipment__id', 'building__id', 'building__name', 'building__address',
            'building__description', 'start', 'end',
        }

        for raw_key, raw_val in request.query_params.items():
            logger.info(f"Got param: {raw_key} = {raw_val}")

            key_for_reserved = raw_key.split('__', 1)[0]
            if key_for_reserved in reserved:
                continue

            if '__' in raw_key:
                key, op = raw_key.split('__', 1)
                lookup = f'equipment__details__{key}__{op}'
            else:
                key = raw_key
                lookup = f'equipment__details__{key}__exact'

            logger.info(f"Using lookup: {lookup}")

            try:
                val = int(raw_val)
            except ValueError:
                if 'contains' in lookup:
                    val = [v.strip() for v in raw_val.split(',')]
                else:
                    val = raw_val

            q &= Q(**{lookup: val})
            logger.info(f"Current Q object: {q}")

        return queryset.filter(q)

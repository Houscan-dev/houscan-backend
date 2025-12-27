from django.db import migrations

def fix_housinginfo_type(apps, schema_editor):
    HousingInfo = apps.get_model('announcements', 'HousingInfo')

    for obj in HousingInfo.objects.all():
        value = obj.type

        # 이미 JSON(dict)이면 패스
        if isinstance(value, dict):
            continue

        if value in [None, '', []]:
            obj.type = None
        else:
            # 문자열 → JSON으로 wrapping
            obj.type = {"value": value}

        obj.save(update_fields=['type'])


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0012_housinginfo_house_type_housinginfo_supply_households_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_housinginfo_type),
    ]

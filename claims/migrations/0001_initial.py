from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Claim",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_filename", models.CharField(blank=True, default="", max_length=255)),
                ("raw_text", models.TextField()),
                ("extracted_fields", models.JSONField(default=dict)),
                ("missing_fields", models.JSONField(default=list)),
                (
                    "recommended_route",
                    models.CharField(
                        choices=[
                            ("Investigation Flag", "Investigation Flag"),
                            ("Manual Review", "Manual Review"),
                            ("Specialist Queue", "Specialist Queue"),
                            ("Fast-Track", "Fast-Track"),
                            ("Standard Review", "Standard Review"),
                        ],
                        max_length=32,
                    ),
                ),
                ("reasoning", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]

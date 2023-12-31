# Generated by Django 2.2 on 2021-07-26 12:54
import json

from django.db import migrations, models


def set_complexity_default(apps, schema_editor):
    grade_dict = {"COMPLEX": 5, "ADBC": 1, "IMGTOOL": 5, "switchBlock": 5, "Job": 5}
    Job = apps.get_model("apiv1", "Job")
    for job in Job.objects.filter(job_deleted=False).all():
        final_complexity = 0
        for flow in job.job_flow.all():
            try:
                flow_path = flow.ui_json_file
                ui_json = json.loads(str(flow_path.read(), 'utf-8'))
            except Exception as e:
                continue
            for block in ui_json.get("nodeDataArray", []):
                try:
                    if block.get("category") in ["switchBlock", "Job"]:
                        final_complexity += grade_dict.get(block.get("category"), 0)
                    elif block.get("unitLists") is not None:
                        unit_list = json.loads(block.get("unitLists")) if isinstance(block.get("unitLists"),
                                                                                     str) else block.get("unitLists",
                                                                                                         {})
                        node_data = unit_list.get("nodeDataArray", [])
                        for unit in node_data:
                            if unit.get("category") == "Unit":
                                unit_type = unit.get("unitMsg", {}).get("execModName")
                                final_complexity += grade_dict.get(unit_type, 0)
                except AttributeError  as e:
                    continue
        job.complexity = final_complexity
        job.save()


class Migration(migrations.Migration):
    dependencies = [
        ('apiv1', '0085_auto_20210720_1945'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='complexity',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='复杂度'),
        ),
        migrations.RunPython(set_complexity_default, ),
        migrations.AlterField(
            model_name='job',
            name='complexity',
            field=models.IntegerField(default=0, verbose_name='复杂度'),
        ),
    ]

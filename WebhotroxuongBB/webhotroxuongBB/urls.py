from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about", views.about, name="about"),
    path("inlaitem", views.inlaitem, name="inlaitem"),
    path("generate_excel/", views.generate_excel, name="generate_excel"),
    path("kiemtratemquetbb", views.kiemtratemquetbb, name="kiemtratemquetbb"),
    path("kiemtramokhoabb", views.kiemtramokhoabb, name="kiemtramokhoabb"),
    path("insert-databaetembb/", views.insert_databaetembb, name="insert_databaetembb"),
    path("kv1tokv2", views.kv1tokv2, name="kv1tokv2"),
    path("tembbcusangkd", views.tembbcusangkd, name="tembbcusangkd"),
    path(
        "kiemtratieuchuantheomay",
        views.kiemtratieuchuantheomay,
        name="kiemtratieuchuantheomay",
    ),
    path(
        "kiemtratieuchuantheomay/weigh",
        views.kiemtratieuchuantheomay_weigh,
        name="kiemtratieuchuantheomay_weigh",
    ),
    path("temoembb/", views.temoembb, name="temoembb"),
]

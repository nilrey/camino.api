# EndPoints config

# EndPoint External - роуты для отправки уведомлений в RestApi
endpoints_external = {
    "ann_archive_on_save": "/ann/{ann_id}/archive/on_save"
}

# EndPoint Internal - описание собственных роутов в текущем Backend
endpoints_internal = {
    "ann_save": {
        "route": "/ann/{annId}/archive/save", 
        "tags": ["ИНС"], 
        "summary": "Выгрузка ИНС (Docker-образа и файла весов) в архив" 
    }
    # заполнить для всех веток роутов
}
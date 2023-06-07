from models import TemplateCategoriesModel


class TemplateCategoriesServices:

    @staticmethod
    def get_categories():
        return TemplateCategoriesModel.find({
            'is_active': True
        })

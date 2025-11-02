import asyncio
from typing import List, Dict
from kivy.lang import Builder
from kivy.clock import mainthread
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.spinner import MDSpinner

# Ceci est juste un test
# --- Importation des Services ---
try:
    from Back.StatsReport import (
        get_prospect_status_distribution,
        get_conversion_rate,
        get_user_conversion_performance
    )

except ImportError:
    print("ATTENTION: Les services de reporting n'ont pas pu être importés. Utilisation de données simulées.")


    # --- SIMULATION DES DONNÉES EN CAS D'IMPORT ERROR ---
    async def get_prospect_status_distribution():
        await asyncio.sleep(0.1)
        return [{'status': 'nouveau', 'count': 45}, {'status': 'interesse', 'count': 30},
                {'status': 'converti', 'count': 8}]


    async def get_conversion_rate():
        await asyncio.sleep(0.1)
        return {"total_converti": 8, "total_prospects": 83, "taux_conversion": "9.64%"}


    async def get_user_conversion_performance():
        await asyncio.sleep(0.1)
        return [
            {"username": "Commercial_A", "total_prospects": 35, "total_converti": 6, "taux_conversion": "17.14%"},
            {"username": "Commercial_B", "total_prospects": 48, "total_converti": 2, "taux_conversion": "4.17%"},
        ]
    # ----------------------------------------------------

# --- KivyMD KV Language ---
KV = '''
<ReportingScreen>:
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: self.theme_cls.bg_light
        spacing: "15dp"
        padding: "15dp"

        MDLabel:
            text: "TABLEAU DE BORD STATISTIQUES"
            halign: "center"
            font_style: "H4"
            adaptive_height: True

        MDScrollView:
            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: "20dp"
                padding: "5dp"
                id: main_stats_container

        MDSpinner:
            id: loading_spinner
            size_hint: None, None
            size: "40dp", "40dp"
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            active: False 
'''


# --- Classe d'Écran ---
class ReportingScreen(MDScreen):
    """ Écran KivyMD pour le reporting et les statistiques. """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "reporting_screen"

    def on_enter(self):
        """ Appelé lorsque l'écran devient visible. """
        if not hasattr(self.ids, 'main_stats_container'):
            Builder.load_string(KV)
        self.load_all_stats()

    def load_all_stats(self):
        """ Démarre le chargement asynchrone de toutes les statistiques. """
        self.ids.loading_spinner.active = True
        self.ids.main_stats_container.clear_widgets()
        asyncio.ensure_future(self._fetch_and_display_all_stats())

    async def _fetch_and_display_all_stats(self):
        """ Exécute toutes les requêtes asynchrones et met à jour l'UI. """
        conversion_data = await get_conversion_rate()
        status_data = await get_prospect_status_distribution()
        performance_data = await get_user_conversion_performance()
        self._update_ui_with_data(conversion_data, status_data, performance_data)

    @mainthread
    def _update_ui_with_data(self, conversion: Dict, status_list: List[Dict], performance_list: List[Dict]):
        """ Met à jour l'interface utilisateur sur le thread principal de Kivy. """
        self.ids.loading_spinner.active = False
        container = self.ids.main_stats_container

        # --- Carte 1: Taux de Conversion Global ---
        card1 = self._create_card("Taux de Conversion Global (Prospect -> Converti)", "card_conversion")

        # ADAPTATION ICI: Utilisation de TwoLineListItem
        card1.add_widget(
            TwoLineListItem(
                text=f"Total Prospects: {conversion['total_prospects']}",
                secondary_text=f"Total Convertis: {conversion['total_converti']}"
            )
        )
        card1.add_widget(MDLabel(
            text=f"[b]{conversion['taux_conversion']}[/b]",
            halign="center",
            font_style="H3",
            markup=True
        ))
        container.add_widget(card1)

        # --- Carte 2: Distribution des Statuts ---
        card2 = self._create_card("Répartition des Prospects par Statut", "card_status")
        status_md_list = MDList()
        if status_list:
            for item in status_list:
                # ADAPTATION ICI: Utilisation de TwoLineListItem
                status_md_list.add_widget(
                    TwoLineListItem(
                        text=f"{item['status'].capitalize()}",
                        secondary_text=f"Nombre: {item['count']}"
                    )
                )
            # Ajout du MDList dans un ScrollView pour gérer l'espace
            card2.add_widget(MDScrollView(
                MDBoxLayout(size_hint_y=None, height=status_md_list.minimum_height, add_widget=status_md_list)))
        else:
            card2.add_widget(MDLabel(text="Aucune donnée de statut.", halign="center"))

        container.add_widget(card2)

        # --- Carte 3: Performance Commerciale ---
        card3 = self._create_card("Taux de Conversion par Commercial", "card_performance")
        performance_md_list = MDList()
        if performance_list:
            for item in performance_list:
                # ADAPTATION ICI: Utilisation de TwoLineListItem
                performance_md_list.add_widget(
                    TwoLineListItem(
                        text=f"{item['username']}",
                        secondary_text=f"Taux: {item['taux_conversion']} ({item['total_converti']}/{item['total_prospects']})"
                    )
                )
            card3.add_widget(MDScrollView(MDBoxLayout(size_hint_y=None, height=performance_md_list.minimum_height,
                                                      add_widget=performance_md_list)))
        else:
            card3.add_widget(MDLabel(text="Aucune donnée de performance.", halign="center"))

        container.add_widget(card3)

    def _create_card(self, title: str, card_id: str) -> MDCard:
        """ Fonction utilitaire pour créer une carte standard. """
        card = MDCard(
            id=card_id,
            orientation="vertical",
            padding="10dp",
            spacing="10dp",
            size_hint_y=None,
            height="300dp",
            elevation=5
        )
        card.add_widget(MDLabel(text=f"[b]{title}[/b]", halign="left", font_style="Subtitle1", markup=True))
        card.add_widget(MDBoxLayout(size_hint_y=None, height="1dp", md_bg_color=(0.5, 0.5, 0.5, 1)))
        return card


# --- Application de Test ---
class ReportingApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.screen = ReportingScreen()
        # Builder.load_string est déplacé ici si l'initialisation dans __init__ pose problème
        if not self.screen.ids:
            Builder.load_string(KV)
        return self.screen


if __name__ == '__main__':
    try:
        # Nécessaire pour lancer KivyMD en mode asynchrone
        asyncio.run(ReportingApp().async_run())
    except KeyboardInterrupt:
        print("\nApplication KivyMD arrêtée.")
    except Exception as e:
        print(f"Erreur inattendue au lancement de l'application KivyMD : {e}")
from django.urls import path

from .views import AgentApplicationView, MyAgentView


urlpatterns = [
    path(
        "apply/",
        AgentApplicationView.as_view(),
        name="agent-application",
    ),
    path(
        "me/",
        MyAgentView.as_view(),
        name="my-agent",
    ),
]
from dataclasses import dataclass
from injector import inject
from typing import List
from helper.logger import logger

from model.enforcement import Enforcement

from argocd_client import V1alpha1ApplicationDestination, V1alpha1Application, V1alpha1ApplicationSpec, \
    ApplicationServiceApi, V1ObjectMeta, V1alpha1SyncPolicy, V1alpha1SyncPolicyAutomated, \
    V1alpha1ApplicationList


@inject
@dataclass
class EnforcementRepository:
    _application_service: ApplicationServiceApi

    def create_enforcement(self, enforcement: Enforcement):

        application = V1alpha1Application(
            metadata=V1ObjectMeta(
               name=enforcement.name,
               labels=enforcement.labels
            ),
            spec=V1alpha1ApplicationSpec(
                destination=V1alpha1ApplicationDestination(
                    name=enforcement.cluster_name
                ),
                source=enforcement.render(),
                sync_policy=V1alpha1SyncPolicy(
                    automated=V1alpha1SyncPolicyAutomated(
                        prune=False,
                        self_heal=True,
                    )
                )
            )
        )

        self._application_service.create_mixin9(application)

    def remove_enforcement(self, enforcement: Enforcement):

        application = V1alpha1Application(
            metadata=V1ObjectMeta(
               name=enforcement.name
            )
        )

        self._application_service.delete_mixin9(application.metadata.name, cascade=False)
        logger.info(f"Application {application.metadata.name} removed")

    def list_installed_enforcements(self, **filters) -> List[Enforcement]:
        labels = self._make_labels(filters)
        application_list: V1alpha1ApplicationList = self._application_service.list_mixin9(
            selector=labels
        )

        if not application_list.items:
            return []

        applications: List[V1alpha1Application] = application_list.items

        enforcements = [
            self._make_enforcement_by_application(application)
            for application in applications
        ]

        return enforcements

    def _make_labels(self, labels) -> str:
        list_labels = [f"{t[0]}={t[1]}" for t in list(labels.items())]
        separator = ","
        return separator.join(list_labels)

    def _make_enforcement_by_application(self, application: V1alpha1Application) -> Enforcement:
        return Enforcement(
            name=application.metadata.name,
            repo=application.spec.source.repo_url,
            path=application.spec.source.path,
            cluster_name=application.metadata.labels['cluster'],
            _labels=application.metadata.labels
        )
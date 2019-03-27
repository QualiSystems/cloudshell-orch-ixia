#!/usr/bin/python
# -*- coding: utf-8 -*-
from cloudshell.workflow.orchestration.setup.default_setup_logic import DefaultSetupLogic

TARGET_TYPE_RESOURCE = 'Resource'
REMAP_CHILD_RESOURCES = 'connect_child_resources'

IXVM_CHASSIS_MODEL = "IxVM Virtual Traffic Chassis 2G"
VYOS_MODEL = "Vyos"
RE_AUTOLOAD_MODELS = [IXVM_CHASSIS_MODEL, VYOS_MODEL]
RE_CONNECT_CHILD_RESOURCES_MODELS = [IXVM_CHASSIS_MODEL]


class IxiaSetupWorkflow(object):
    def __init__(self, execute_autoload=True, execute_remap_connections=True):
        """

        :param execute_autoload:
        :param execute_remap_connections:
        """
        self.execute_autoload = execute_autoload
        self.execute_remap_connections = execute_remap_connections

    def register(self, sandbox):
        """

        :param sandbox:
        :return:
        """
        sandbox.logger.info("Adding Ixia setup orchestration")
        sandbox.workflow.on_configuration_ended(function=self.execute_autoload_on_ixvm,
                                                components=sandbox.components.apps)

    def execute_autoload_on_ixvm(self, sandbox, components):
        """Execute Autoload on the deployed Virtual IxVM Chassis"""

        deployed_apps_names = [app.deployed_app.Name for app in components.values()]

        resource_details_cache = {app_name: sandbox.automation_api.GetResourceDetails(app_name) for app_name in
                                  deployed_apps_names}

        # execute autoload on the deployed apps after they've got IPs
        if self.execute_autoload:
            for app_name in deployed_apps_names:
                app_resource_details = resource_details_cache[app_name]

                if app_resource_details.ResourceModelName not in RE_AUTOLOAD_MODELS:
                    continue

                sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                                       message='Autoload resource {}'.format(app_name))

                sandbox.automation_api.AutoLoad(app_name)

        # execute remap connections on the deployed apps after correct autoload(s)
        if self.execute_remap_connections:
            for app_name in deployed_apps_names:
                app_resource_details = resource_details_cache[app_name]

                if app_resource_details.ResourceModelName not in RE_CONNECT_CHILD_RESOURCES_MODELS:
                    continue

                sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                                       message='Connect Child resource on {}'.format(app_name))

                sandbox.logger.info("Triggering Connect Child resources command on {}".format(app_name))
                sandbox.automation_api.ExecuteCommand(sandbox.id,
                                                      app_name,
                                                      TARGET_TYPE_RESOURCE,
                                                      REMAP_CHILD_RESOURCES, [])

            sandbox.logger.info("Triggering 'connect_all_routes_in_reservation' method from the DefaultSetupLogic")
            sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                                   message='Connecting routes in the reservation')

            reservation_details = sandbox.automation_api.GetReservationDetails(sandbox.id)

            DefaultSetupLogic.connect_all_routes_in_reservation(api=sandbox.automation_api,
                                                                reservation_details=reservation_details,
                                                                reservation_id=sandbox.id,
                                                                resource_details_cache=resource_details_cache,
                                                                logger=sandbox.logger)

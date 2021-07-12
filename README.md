# OpenMotics HomeAssistant integration

### Custom integration to control an [OpenMotics](https://www.openmotics.com/en/) platform via HomeAssistant

<!-- TOC -->

- [INTRODUCTION](#introduction)
- [HOW TO INSTALL](#how-to-install)
  - [1. Grant permissions for Python to have rootless access to the HCI interface](#1-grant-permissions-for-python-to-have-rootless-access-to-the-hci-interface)
  - [2. Install the custom integration](#2-install-the-custom-integration)
  - [3. Add your sensors to the MiHome app if you haven’t already](#3-add-your-sensors-to-the-mihome-app-if-you-havent-already)
  - [4. Configure the integration](#4-configure-the-integration)
    - [4a. Configuration in the User Interface](#4a-configuration-in-the-user-interface)
    - [4b. Configuration in YAML](#4b-configuration-in-yaml)
- [CONFIGURATION PARAMETERS](#configuration-parameters)
  - [Configuration parameters at component level](#configuration-parameters-at-component-level)
  - [Configuration parameters at device level](#configuration-parameters-at-device-level)
  - [Configuration in the User Interface](#configuration-in-the-user-interface)
  - [Configuraton in YAML](#configuraton-in-yaml)
  - [Deleting devices and sensors](#deleting-devices-and-sensors)
- [FREQUENTLY ASKED QUESTIONS](#frequently-asked-questions)
- [CREDITS](#credits)
- [FORUM](#forum)

<!-- /TOC -->

## INTRODUCTION

This custom component is developed for controlling an [OpenMotics](https://www.openmotics.com/en/) platform by using the cloud-sdk, officailly maintained by the OpenMotics Developer Team. 

## HOW TO INSTALL

### 1. Grant permissions to your OpenMotics installation

Login to [cloud.openmotics.com](https://cloud.openmotics.com/)

![login](/pictures/login.cloud.openmotics.png)

Remember to use your e-mail address as login. 

Make sure your installation is at a recent firmware. Update if needed.

![firmware](/pictures/update01.png)

Create an additional user

[user01](/pictures/user01.png)

[user02](/pictures/user02.png)

[user03](/pictures/user03.png)

[user04](/pictures/user04.png)

Make sure the Client type is `Confidential` and the Grant type is `Client credentials`.
The Redirect URI is not used right now and can have any value.

[user05](/pictures/user05.png)

Copy the Client ID and Client secret as you'll need it to configure the integration in Home Assistant.

### 2. Install Home Assistant Core

See [Home Assistant Official Installation Guide](https://www.home-assistant.io/installation/) to install Home Assistant Core.

### 3. Install the custom integration

Option 1: Copy Method
  1. Download the [openmotics-home-assistant repo](https://github.com/openmotics/home-assistant).
  2. Unzip it and copy the `custom_components/openmotics` folder to the Home Assistant configuration directory, for example `~/.homeassistant`.

  ![configuration directory](/pictures/directory.png)

  The disadvantage of a manual installation is that you won't be notified about updates.

Option 2: HACS installation

  1. See [HACS Official Installation Guide](https://hacs.xyz/docs/installation/installation/) and install HACS.
  2. See [Initial Configuration Guide](https://hacs.xyz/docs/configuration/basic) and complete initial configuration.
  3. Open Home Assistant. Click HACS > Integrations > ⋮ > Custom repositories.

  ![custom repository](/pictures/custom_repository.png)

  4. Enter `https://github.com/openmotics/home-assistant.git` in the address bar at the bottom left of the window. Select Integration from the Category list and click ADD.

  ![github](/pictures/github.png)

  5. In the dialog box that appears, click INSTALL.

  ![install](/pictures/install.png)


### 4. Configure the integration.

Make sure you restart Home Assistant after the installation in HACS. After the restart, go to **Configuration** in the side menu in Home Assistant and select **Integrations**. Click on **Add Integrations** in the bottom right corner and search for **Openmotics** to install. This will open the configuration menu with the default settings.

  ![Integration setup](/pictures/configuration_screen.png)

Fill in the user_id and secret_id you have created in the first step.

Depending on your installation, the modules should be added to your Home Assistant automatically within a few seconds till 10 minutes.

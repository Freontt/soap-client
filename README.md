# SOAP-клиент для общения с сервисами по WSDL контракту

Данная библиотека предоставляет удобную обёртку для использования SOAP-клиента из библиотеки zeep. Оболочка предназначена в первую очередь для асинхронных приложений.

Библиотека состоит из следующих компонентов:
- [exceptions.py](src/soap_client/exceptions.py): Исключения библиотеки.
- [manager.py](src/soap_client/manager.py): Manager для управления клиентом.
- [registry.py](src/soap_client/registry.py): Класс-реестр всех SOAP-клиентов.
- [settings.py](src/soap_client/settings.py): Настройки для управления клиентом.


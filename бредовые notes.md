* Пока устройство не добавлено в контроллер, у него нет id. hash_id отсутствует, как минимум, у USG. Будем надеяться, что хотя бы MAC есть всегда и он не меняется :)
* В ветке /stat/sta по сайту есть "ap_mac", но для не-AP оно неактуально. Но пусть будет
* Внезапно, параметр last_seen отсутствует не только для новых девайсов, но и для некоторых в статусе Adopted. Как так - хз
* Satisfaction - не очень понятный параметр. Хз, надо ли оно вообще - отсутствует для GW, а для SW всегда 100. В связи с этим, параметр в шаблоне отключен, а в скрипте две строки, которые к нему относятся - закомментированы. * Если нужен - включать по вкусу
* Для свитчей можно собирать данные о температуре, перегреве и сколько ватт они отдают.

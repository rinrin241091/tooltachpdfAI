import type { AgCoreBeanCollection } from '../interfaces/agCoreBeanCollection';
import type { BaseEvents } from '../interfaces/baseEvents';
import type { BaseProperties } from '../interfaces/baseProperties';
import type { IAriaAnnouncementService } from '../interfaces/iAriaAnnouncementService';
import type { IPropertiesService } from '../interfaces/iProperties';
import { AgBeanStub } from './agBeanStub';
export declare class BaseAriaAnnouncementService<TBeanCollection extends AgCoreBeanCollection<TProperties, TGlobalEvents, TCommon, TPropertiesService>, TProperties extends BaseProperties, TGlobalEvents extends BaseEvents, TCommon, TPropertiesService extends IPropertiesService<TProperties, TCommon>> extends AgBeanStub<TBeanCollection, TProperties, TGlobalEvents, TCommon, TPropertiesService> implements IAriaAnnouncementService {
    beanName: "ariaAnnounce";
    private descriptionContainer;
    private readonly pendingAnnouncements;
    private lastAnnouncement;
    constructor();
    postConstruct(): void;
    /**
     * @param key used for debouncing calls
     */
    announceValue(value: string, key: string): void;
    private updateAnnouncement;
    private handleAnnouncementUpdate;
    destroy(): void;
}

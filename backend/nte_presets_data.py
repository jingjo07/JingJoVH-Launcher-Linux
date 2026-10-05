"""Pinned snapshot of AlteriaX/NTE-Configs."""

SOURCE_URL = "https://github.com/AlteriaX/NTE-Configs"
SOURCE_REVISION = "d749de0579315f61c2046c960d1c5756595171ff"

PRESET_INFO = {
    "config-1": "RTX 4070 / RX 6900 XT trở lên",
    "config-2": "RTX 3060 Ti–4060 Ti / RX 6700 XT–7800 XT",
    "config-3": "RTX 3050–3060 / GTX 1660 / RX 5600 XT–6600 XT",
    "config-4": "GTX 1060–1660 / RX 570–6500 XT",
    "config-5": "GTX 1050 Ti trở xuống / iGPU",
}

PRESETS = {
    "config-1": """[SystemSettings]
; --- Post Processing ---
;r.FilmGrain=0
;r.Tonemapper.Quality=0
;r.DOF.Kernel.MaxBackgroundRadius=0
;r.DOF.Kernel.MaxForegroundRadius=0
;r.LightShaftBloomQuality=0
r.SceneColorFringeQuality=0
r.PostProcessing.DownsampleQuality=1
r.PostProcessing.QuarterResolutionDownsample=0
; --- Shadows ---
r.Shadow.RadiusThreshold=0
r.Shadow.MinResolution=1024
r.Shadow.MaxResolution=2048
r.Shadow.MaxCSMResolution=4096
r.Shadow.DistanceScale=1.0
r.Shadow.PreShadowResolutionFactor=1.0
r.Shadow.FarCascadesResolutionRatio=1.0
; --- Ambient Occlusion ---
r.DFFullResolution=1
r.DistanceFieldAO=1
r.AO.AllowLowNumConeSteps=0
r.AOQuality=1
r.AmbientOcclusion.DistanceCulling=1
r.AmbientOcclusionMaxQuality=100
r.SkylightIntensityMultiplier=1.0
; --- View Distance / LoD / Material Quality ---
r.StaticMeshLODDistanceScale=0.1
r.MaterialQualityLevel=1
r.ViewDistanceScale=5.0
foliage.LODDistanceScale=1.5
r.LightMaxDrawDistanceScale=1.0
wp.Runtime.GridLoadingRangeLevel=3
wp.Runtime.GridLoadingRangeScale=1.2
wp.Runtime.HLODLoadingRangeScale=1.2
; --- Streaming / Texture ---
r.MaxAnisotropy=16
r.Streaming.Boost=1.25
r.Streaming.UseAllMips=1
; --- Reflections / Others ---
r.Lumen.Reflections.SmoothBias=0.55
r.SSR.HalfResSceneColor=0
r.SSR.MaxRoughness=0.65
r.LightShaftDownSampleFactor=1
a.URO.ForceAnimRate=1
r.Upscale.Quality=3
r.UIRenderTargetQuality=100.0
r.Emitter.FastPoolEnable=1
r.EmitterSpawnRateScale=1.0
r.LightingChannelsDownsampleFactor=1
; --- Anti-aliasing ---
r.SMAA.Quality=3
r.SMAA.MaxSearchSteps=32
r.SMAA.MaxSearchStepsDiagonal=16
r.TemporalAA.Quality=3
r.TemporalAA.QualityForToon=3
r.TemporalAACurrentFrameWeight=0.25
r.TemporalAAFilterSize=0.1
r.TemporalAASamples=4
; --- NPC / Vehicle Density ---
MassParkedVehicleSpawner.MassParkedVehicleSpawnerScale=1.5
HTMassCrowdSpawner.HTMassCrowdSpawnerScale=1.1
UHTMassCrowdForceLODProcessor.MaxLODHighCount=6
UHTMassCrowdForceLODProcessor.MaxLODMediumCount=19
UHTMassCrowdForceLODProcessor.MaxLODLowCount=110
HTMassVehicleSpawner.HTMassVehicleSpawnerScale=1.1
UHTMassVehicleForceLodProcessor.MaxLODHighCount=6
UHTMassVehicleForceLodProcessor.MaxLODMediumCount=11
UHTMassVehicleForceLodProcessor.MaxLODLowCount=100
HTAISpawnCache.DriveVehicleDensity=1.1

; --- UI Scale ---
[/Script/Engine.UserInterfaceSettings]
ApplicationScale=1.0

; --- Logging ---
[Core.Log]
global=none
""",
    "config-2": """[SystemSettings]
; --- Post Processing ---
;r.FilmGrain=0
;r.Tonemapper.Quality=0
;r.DOF.Kernel.MaxBackgroundRadius=0
;r.DOF.Kernel.MaxForegroundRadius=0
;r.LightShaftBloomQuality=0
r.SceneColorFringeQuality=0
r.PostProcessing.DownsampleQuality=1
r.PostProcessing.QuarterResolutionDownsample=0
; --- Shadows ---
r.Shadow.RadiusThreshold=0
r.Shadow.MinResolution=768
r.Shadow.MaxResolution=1024
r.Shadow.MaxCSMResolution=2048
r.Shadow.DistanceScale=0.85
r.Shadow.PreShadowResolutionFactor=1.0
r.Shadow.FarCascadesResolutionRatio=1.0
; --- Ambient Occlusion ---
r.DistanceFieldAO=1
r.AO.AllowLowNumConeSteps=0
r.AOQuality=1
r.AmbientOcclusion.DistanceCulling=1
r.AmbientOcclusionMaxQuality=100
r.SkylightIntensityMultiplier=1.0
; --- View Distance / LoD / Material Quality ---
r.StaticMeshLODDistanceScale=0.1
r.MaterialQualityLevel=1
r.ViewDistanceScale=5.0
foliage.LODDistanceScale=1.0
r.LightMaxDrawDistanceScale=1.0
wp.Runtime.GridLoadingRangeLevel=2
wp.Runtime.GridLoadingRangeScale=1.0
wp.Runtime.HLODLoadingRangeScale=1.0
; --- Streaming / Texture ---
r.MaxAnisotropy=16
r.Streaming.Boost=1.0
r.Streaming.UseAllMips=1
; --- Reflections / Others ---
r.Lumen.Reflections.SmoothBias=0.55
r.SSR.HalfResSceneColor=0
r.SSR.MaxRoughness=0.65
r.LightShaftDownSampleFactor=1
a.URO.ForceAnimRate=1
r.Upscale.Quality=3
r.UIRenderTargetQuality=100.0
r.Emitter.FastPoolEnable=1
r.EmitterSpawnRateScale=1.0
r.LightingChannelsDownsampleFactor=1
; --- Anti-aliasing ---
r.SMAA.Quality=3
r.SMAA.MaxSearchSteps=32
r.SMAA.MaxSearchStepsDiagonal=16
r.TemporalAA.Quality=3
r.TemporalAA.QualityForToon=3
r.TemporalAACurrentFrameWeight=0.25
r.TemporalAAFilterSize=0.1
r.TemporalAASamples=4
; --- NPC / Vehicle Density ---
MassParkedVehicleSpawner.MassParkedVehicleSpawnerScale=1.25
HTMassCrowdSpawner.HTMassCrowdSpawnerScale=1.05
UHTMassCrowdForceLODProcessor.MaxLODHighCount=5
UHTMassCrowdForceLODProcessor.MaxLODMediumCount=18
UHTMassCrowdForceLODProcessor.MaxLODLowCount=105
HTMassVehicleSpawner.HTMassVehicleSpawnerScale=1.05
UHTMassVehicleForceLodProcessor.MaxLODHighCount=5
UHTMassVehicleForceLodProcessor.MaxLODMediumCount=10
UHTMassVehicleForceLodProcessor.MaxLODLowCount=95
HTAISpawnCache.DriveVehicleDensity=1.0

; --- UI Scale ---
[/Script/Engine.UserInterfaceSettings]
ApplicationScale=1.0

; --- Logging ---
[Core.Log]
global=none
""",
    "config-3": """[SystemSettings]
; --- Post Processing ---
;r.FilmGrain=0
;r.Tonemapper.Quality=0
;r.DOF.Kernel.MaxBackgroundRadius=0
;r.DOF.Kernel.MaxForegroundRadius=0
;r.LightShaftBloomQuality=0
r.SceneColorFringeQuality=0
r.PostProcessing.DownsampleQuality=1
r.PostProcessing.QuarterResolutionDownsample=0
; --- Shadows ---
r.Shadow.RadiusThreshold=0.01
r.Shadow.MinResolution=512
r.Shadow.MaxResolution=1024
r.Shadow.MaxCSMResolution=2048
r.Shadow.DistanceScale=0.85
r.Shadow.PreShadowResolutionFactor=1.0
r.Shadow.FarCascadesResolutionRatio=1.0
; --- Ambient Occlusion ---
r.AO.AllowLowNumConeSteps=0
r.AOQuality=1
r.AmbientOcclusion.DistanceCulling=1
r.AmbientOcclusionMaxQuality=100
; --- View Distance / LoD / Material Quality ---
r.StaticMeshLODDistanceScale=0.25
r.MaterialQualityLevel=1
r.ViewDistanceScale=3.0
foliage.LODDistanceScale=1.0
r.LightMaxDrawDistanceScale=1.0
wp.Runtime.GridLoadingRangeLevel=2
wp.Runtime.GridLoadingRangeScale=0.9
wp.Runtime.HLODLoadingRangeScale=1.0
; --- Streaming / Texture ---
r.MaxAnisotropy=16
r.Streaming.Boost=1.0
; Optional lower pool size for 6GB VRAM GPU to reduce out of VRAM FPS drop
;r.Streaming.PoolSize=1024
r.Streaming.UseAllMips=1
; --- Reflections / Others ---
r.Lumen.Reflections.SmoothBias=0.55
r.SSR.HalfResSceneColor=0
r.SSR.MaxRoughness=0.65
r.LightShaftDownSampleFactor=1
a.URO.ForceAnimRate=1
r.Upscale.Quality=3
r.UIRenderTargetQuality=100.0
r.Emitter.FastPoolEnable=1
r.EmitterSpawnRateScale=0.5
r.LightingChannelsDownsampleFactor=2
; --- Anti-aliasing ---
r.SMAA.Quality=3
r.SMAA.MaxSearchSteps=32
r.SMAA.MaxSearchStepsDiagonal=16
r.TemporalAA.Quality=3
r.TemporalAA.QualityForToon=3
r.TemporalAACurrentFrameWeight=0.25
r.TemporalAAFilterSize=0.1
r.TemporalAASamples=4
; --- NPC / Vehicle Density ---
MassParkedVehicleSpawner.MassParkedVehicleSpawnerScale=1.1
HTAISpawnCache.DriveVehicleDensity=0.8

; --- UI Scale ---
[/Script/Engine.UserInterfaceSettings]
ApplicationScale=1.0

; --- Logging ---
[Core.Log]
global=none
""",
    "config-4": """; If you need more FPS, use TAA and lower rendering accuracy to 0.8 or lower

[SystemSettings]
; --- Post Processing ---
;r.FilmGrain=0
;r.Tonemapper.Quality=0
;r.DOF.Kernel.MaxBackgroundRadius=0
;r.DOF.Kernel.MaxForegroundRadius=0
;r.LightShaftBloomQuality=0
r.SceneColorFringeQuality=0
; --- Shadows ---
r.Shadow.RadiusThreshold=0.01
r.Shadow.MinResolution=256
r.Shadow.MaxResolution=512
r.Shadow.MaxCSMResolution=1024
r.Shadow.DistanceScale=0.7
r.Shadow.PreShadowResolutionFactor=0.75
r.Shadow.FarCascadesResolutionRatio=0.75
; --- Ambient Occlusion ---
r.DistanceFieldAO=0
r.AmbientOcclusionMaxQuality=100
r.SkylightIntensityMultiplier=0.8
; --- View Distance / LoD / Material Quality ---
r.StaticMeshLODDistanceScale=0.5
r.MaterialQualityLevel=1
r.ViewDistanceScale=1.5
foliage.LODDistanceScale=0.9
r.LightMaxDrawDistanceScale=1.0
wp.Runtime.GridLoadingRangeLevel=1
wp.Runtime.GridLoadingRangeScale=0.8
wp.Runtime.HLODLoadingRangeScale=0.9
; --- Streaming / Texture ---
r.MaxAnisotropy=16
r.Streaming.Boost=1.0
r.Streaming.PoolSize=1024
r.Streaming.UseAllMips=1
; --- Reflections / Others ---
r.Lumen.Reflections.SmoothBias=0.55
r.SSR.HalfResSceneColor=0
r.SSR.MaxRoughness=0.65
r.LightShaftDownSampleFactor=2
a.URO.ForceAnimRate=1
r.Upscale.Quality=3
r.UIRenderTargetQuality=100.0
r.Emitter.FastPoolEnable=1
r.EmitterSpawnRateScale=0.25
r.LightingChannelsDownsampleFactor=4
; --- Anti-aliasing ---
r.SMAA.Quality=3
r.SMAA.MaxSearchSteps=32
r.SMAA.MaxSearchStepsDiagonal=16
r.TemporalAA.Quality=3
r.TemporalAA.QualityForToon=3
r.TemporalAACurrentFrameWeight=0.25
r.TemporalAAFilterSize=0.1
r.TemporalAASamples=4
r.TemporalAA.Upsampling=1

; --- UI Scale ---
[/Script/Engine.UserInterfaceSettings]
ApplicationScale=1.0

; --- Logging ---
[Core.Log]
global=none
""",
    "config-5": """; If you need more FPS, use TAA and lower rendering accuracy to 0.8 or lower

[SystemSettings]
; --- Post Processing ---
;r.FilmGrain=0
;r.Tonemapper.Quality=0
;r.DOF.Kernel.MaxBackgroundRadius=0
;r.DOF.Kernel.MaxForegroundRadius=0
;r.LightShaftBloomQuality=0
r.SceneColorFringeQuality=0
; --- Shadows ---
r.Shadow.RadiusThreshold=0.04
r.Shadow.MinResolution=128
r.Shadow.MaxResolution=512
r.Shadow.MaxCSMResolution=512
r.Shadow.DistanceScale=0.6
r.Shadow.PreShadowResolutionFactor=0.5
r.Shadow.FarCascadesResolutionRatio=0.5
; --- Ambient Occlusion ---
r.DistanceFieldAO=0
r.AmbientOcclusionMaxQuality=0
r.SkylightIntensityMultiplier=0.8
; --- View Distance / LoD / Material Quality ---
r.StaticMeshLODDistanceScale=0.7
r.MaterialQualityLevel=0
r.ViewDistanceScale=0.8
foliage.LODDistanceScale=0.8
r.LightMaxDrawDistanceScale=0.5
wp.Runtime.GridLoadingRangeLevel=0
; Lower wp.Runtime.GridLoadingRangeScale value if you need more FPS
wp.Runtime.GridLoadingRangeScale=0.6
wp.Runtime.HLODLoadingRangeScale=0.9
; --- Streaming / Texture ---
r.MaxAnisotropy=8
r.Streaming.Boost=1.0
r.Streaming.PoolSize=512
r.Streaming.UseAllMips=1
; --- Reflections / Others ---
r.SSR.HalfResSceneColor=1
r.SSR.MaxRoughness=0.65
r.LightShaftDownSampleFactor=2
a.URO.ForceAnimRate=1
r.Upscale.Quality=3
r.UIRenderTargetQuality=100.0
r.Emitter.FastPoolEnable=1
r.EmitterSpawnRateScale=0.125
r.LightingChannelsDownsampleFactor=8
; --- Anti-aliasing ---
r.SMAA.Quality=3
r.SMAA.MaxSearchSteps=32
r.SMAA.MaxSearchStepsDiagonal=16
r.TemporalAA.Quality=3
r.TemporalAA.QualityForToon=3
r.TemporalAACurrentFrameWeight=0.25
r.TemporalAAFilterSize=0.1
r.TemporalAASamples=4
r.TemporalAA.Upsampling=1

; --- UI Scale ---
[/Script/Engine.UserInterfaceSettings]
ApplicationScale=1.0

; --- Logging ---
[Core.Log]
global=none
""",
}

COMMON = {
    "device_profiles": """[Windows DeviceProfile]
CVars=UI.ShowLumenSettings=1

[Windows_Low DeviceProfile]
CVars=UI.ShowLumenSettings=1

[Windows_Mid DeviceProfile]
CVars=UI.ShowLumenSettings=1

[Windows_High DeviceProfile]
CVars=UI.ShowLumenSettings=1
""",
    "game": """[/Script/MoviePlayer.MoviePlayerSettings]
StartupMovies=
""",
    "input": """[/Script/Engine.InputSettings]
bEnableMouseSmoothing=false
bEnableFOVScaling=false
""",
}

# Upstream blobs intentionally have no trailing newline.
PRESETS = {key: value.rstrip("\n") for key, value in PRESETS.items()}
COMMON = {key: value.rstrip("\n") for key, value in COMMON.items()}
